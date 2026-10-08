"""Exercise quote and payroll persistence against an isolated SQLite database."""

import os
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from sqlalchemy import text

os.environ["DATABASE_MODE"] = "offline"
_test_db = Path(tempfile.gettempdir()) / f"senatrack-test-{uuid4().hex}.sqlite3"
os.environ["LOCAL_DB_PATH"] = _test_db.as_posix()

import app.models  # noqa: E402 - register the SQLAlchemy tables
from app.core.database import Base, LocalAsyncSession, local_async_engine, set_db_session, _apply_non_destructive_alters  # noqa: E402
from app.models.company_model import Company  # noqa: E402
from app.models.employee_model import EmployeeModel  # noqa: E402
from app.models.user_model import User  # noqa: E402
from app.models.tva_rate_model import TvaRateModel  # noqa: E402
from app.schemas.company_schema import CompanySettings  # noqa: E402
from app.routes.company_route import update_company_settings  # noqa: E402
from app.schemas.employee_schema import EmployeePayroll, EmployeePayrollCreate  # noqa: E402
from app.schemas.proforma_schema import Proforma, ProformaCreate, ProformaUpdate  # noqa: E402
from app.schemas.purchase_order_schema import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate  # noqa: E402
from app.services.employee_service import EmployeeService  # noqa: E402
from app.services.proforma_service import ProformaService  # noqa: E402
from app.services.purchase_order_service import PurchaseOrderService  # noqa: E402


class QuotePayrollFlowTest(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        set_db_session(None)
        await local_async_engine.dispose()
        _test_db.unlink(missing_ok=True)

    async def test_quote_and_payroll_round_trip(self):
        async with local_async_engine.begin() as connection:
            # Simulate a deployed table from before the additive details migration.
            await connection.execute(text("CREATE TABLE purchase_orders (id VARCHAR(20) PRIMARY KEY, company_id VARCHAR(64), order_number VARCHAR(100) NOT NULL, supplier_id VARCHAR(64), status VARCHAR(20) NOT NULL, total_amount FLOAT NOT NULL, created_at DATETIME, updated_at DATETIME)"))
            await connection.run_sync(Base.metadata.create_all)
            await _apply_non_destructive_alters(connection, dialect="sqlite")
            columns = await connection.execute(text("PRAGMA table_info(purchase_orders)"))
            self.assertIn("details", {column[1] for column in columns})

        async with LocalAsyncSession() as session:
            set_db_session(session)
            session.add_all([
                User(id="test-user", name="Tester", email="tester@example.invalid", hashed_password="unused"),
                Company(id="test-company", name="Test Company", owner_id="test-user"),
                EmployeeModel(id="test-employee", company_id="test-company", first_name="Awa", last_name="Sene"),
            ])
            await session.commit()

            quote_service = ProformaService()
            quote = await quote_service.create_proforma(
                ProformaCreate.model_validate({
                    "date": "2026-10-08T10:00:00",
                    "client": {"name": "Client test"},
                    "items": [{"description": "Produit", "itemId": "p1", "itemType": "product", "quantity": 2, "sellPrice": 25, "total": 50}],
                    "subtotal": 50, "discount": 0, "tva": 0, "taxAmount": 0, "total": 50,
                    "objet": "Commande test",
                }),
                company_id="test-company", created_by="test-user",
            )
            saved_quote = Proforma.model_validate(quote)
            self.assertEqual(saved_quote.items[0].sell_price, 25)
            self.assertEqual(saved_quote.objet, "Commande test")
            self.assertEqual(len(await quote_service.get_company_proformas("test-company")), 1)
            self.assertIsNone(await quote_service.get_proforma_by_id(saved_quote.id, "another-company"))

            updated = await quote_service.update_proforma(saved_quote.id, "test-company", ProformaUpdate(discount=10, total=45))
            self.assertEqual(updated["discount"], 10)
            self.assertEqual(updated["total"], 45)

            payroll_service = EmployeeService()
            payroll_id = await payroll_service.create_payroll(
                "test-employee", "test-company",
                EmployeePayrollCreate(employeeId="test-employee", periodMonth=10, periodYear=2026,
                                      netSalary=50000, paidDate="2026-10-08"),
            )
            payroll = await payroll_service.get_payroll_by_id(payroll_id, "test-employee", "test-company")
            self.assertIsInstance(payroll, EmployeePayroll)
            self.assertEqual(payroll.employee_name, "Awa Sene")
            self.assertEqual(payroll.period, {"month": 10, "year": 2026})
            self.assertEqual(len(await payroll_service.get_all_payrolls("test-company")), 1)

            order_service = PurchaseOrderService()
            order_payload = PurchaseOrderCreate.model_validate({
                "supplierId": "supplier-1", "supplierName": "Fournisseur test",
                "orderDate": "2026-10-08", "items": [{"id": "line-1", "productId": "p1",
                "productName": "Produit", "quantity": 2, "buyPrice": 25,
                "totalPrice": 50, "unit": "unité"}], "subtotal": 50,
                "taxRate": 0, "taxAmount": 0, "totalAmount": 50, "currency": "FCFA",
            })
            order_id = await order_service.create("test-company", order_payload)
            order = await order_service.get_by_id(order_id, "test-company")
            self.assertIsInstance(order, PurchaseOrder)
            self.assertEqual(order.items[0].buy_price, 25)
            self.assertEqual(order.supplier_name, "Fournisseur test")
            self.assertIsNone(await order_service.get_by_id(order_id, "other-company"))
            await order_service.update(order_id, "test-company", PurchaseOrderUpdate(notes="Livrer vite", totalAmount=55))
            updated_order = await order_service.get_by_id(order_id, "test-company")
            self.assertEqual(updated_order.notes, "Livrer vite")
            self.assertEqual(updated_order.total_amount, 55)

            session.add(TvaRateModel(id="test-rate", company_id="test-company", name="TVA", rate=18, is_default=True, is_active=True))
            await session.commit()
            company = await update_company_settings(
                "test-company",
                CompanySettings.model_validate({"tva": {"enabled": True, "defaultRateId": "test-rate"},
                    "stockAlertThreshold": 5, "allowPriceModification": False}),
                session,
                SimpleNamespace(id="test-user", email="tester@example.invalid", name="Tester"),
            )
            self.assertEqual(company.settings["tva"]["defaultRateId"], "test-rate")
            self.assertEqual(company.settings["stockAlertThreshold"], 5)

if __name__ == "__main__":
    unittest.main()
