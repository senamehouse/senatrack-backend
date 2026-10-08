"""Exercise quote and payroll persistence against an isolated SQLite database."""

import os
import io
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import select, text
from fastapi import HTTPException
from fastapi import UploadFile
from starlette.requests import Request
from starlette.datastructures import Headers

os.environ["DATABASE_MODE"] = "offline"
_test_db = Path(tempfile.gettempdir()) / f"senatrack-test-{uuid4().hex}.sqlite3"
os.environ["LOCAL_DB_PATH"] = _test_db.as_posix()

import app.models  # noqa: E402 - register the SQLAlchemy tables
from app.core.database import Base, LocalAsyncSession, local_async_engine, set_db_session, _apply_non_destructive_alters  # noqa: E402
from app.models.company_model import Company, CompanyMember as CompanyMemberModel, UserCompanyRoleModel, UserCompanyRoleAssignmentModel  # noqa: E402
from app.models.employee_model import EmployeeModel  # noqa: E402
from app.models.user_model import User  # noqa: E402
from app.models.tva_rate_model import TvaRateModel  # noqa: E402
from app.schemas.company_schema import CompanySettings  # noqa: E402
from app.routes.company_route import update_company_settings  # noqa: E402
from app.core.dependencies import ensure_company_access, get_company_id  # noqa: E402
from app.schemas.employee_schema import EmployeePayroll, EmployeePayrollCreate, EmployeeLeaveRequestCreate, EmployeeLeaveRequestUpdate  # noqa: E402
from app.schemas.proforma_schema import Proforma, ProformaCreate, ProformaUpdate  # noqa: E402
from app.schemas.purchase_order_schema import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate  # noqa: E402
from app.schemas.supplier_schema import Supplier, SupplierCreate, SupplierUpdate  # noqa: E402
from app.services.employee_service import EmployeeService  # noqa: E402
from app.services.proforma_service import ProformaService  # noqa: E402
from app.services.purchase_order_service import PurchaseOrderService  # noqa: E402
from app.services.supplier_service import SupplierService  # noqa: E402
from app.services.company_service import CompanyService  # noqa: E402
from app.services.file_service import FileService  # noqa: E402
from app.services.upload_service import UploadService  # noqa: E402
from app.services.activation_key_service import ActivationKeyService  # noqa: E402
from app.schemas.activation_key_schema import ActivationKeyCreate, ActivationKeyUsageResponse  # noqa: E402
from app.services.invitation_service import InvitationService  # noqa: E402
from app.services.user_service import UserService  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402
from app.services.migration_service import MigrationService  # noqa: E402
from app.routes.user_route import update_user_as_admin, update_user_status, update_user_platform_role, update_user  # noqa: E402
from app.schemas.user_schema import UserAdminUpdate, UserStatusUpdate, UserPlatformRoleUpdate, UserUpdate  # noqa: E402
from app.schemas.invitation_schema import CompanyInvitationCreate, CompanyInvitation as CompanyInvitationSchema  # noqa: E402
from app.routes.invitation_route import create_invitation as create_invitation_route, get_pending_invitations as pending_invitations_route  # noqa: E402


class QuotePayrollFlowTest(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        set_db_session(None)
        await local_async_engine.dispose()
        _test_db.unlink(missing_ok=True)

    async def test_role_migration_with_legacy_columns_is_idempotent(self):
        async with local_async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(30)"))
            await connection.execute(text("ALTER TABLE company_members ADD COLUMN role VARCHAR(30)"))

        async with LocalAsyncSession() as session:
            set_db_session(session)
            session.add_all([
                User(id="legacy-admin", name="Admin", email="legacy-admin@example.com", hashed_password="unused"),
                User(id="legacy-member", name="Member", email="legacy-member@example.com", hashed_password="unused"),
                Company(id="legacy-company", name="Legacy", owner_id="legacy-admin"),
                CompanyMemberModel(id="legacy-membership", company_id="legacy-company", user_id="legacy-member"),
            ])
            await session.commit()
            await session.execute(text("UPDATE users SET role = 'admin' WHERE id = 'legacy-admin'"))
            await session.execute(text("UPDATE company_members SET role = 'manager' WHERE id = 'legacy-membership'"))
            await session.commit()

            migration = MigrationService()
            self.assertTrue((await migration.get_migration_status())["migration_needed"])
            first = await migration.run_full_migration()
            self.assertEqual(first["user_migration"]["migrated_users"], 2)
            self.assertEqual(first["company_migration"]["migrated_members"], 2)
            self.assertFalse((await migration.get_migration_status())["migration_needed"])
            self.assertEqual((await migration.run_full_migration())["user_migration"]["migrated_users"], 0)
            self.assertEqual((await migration.run_full_migration())["company_migration"]["migrated_members"], 0)
            self.assertIn("Platform Administrator", [role.name for role in await UserService().get_user_roles("legacy-admin")])
            self.assertIn("Propriétaire", [role.name for role in await CompanyService().get_user_company_roles("legacy-admin", "legacy-company")])
            self.assertIn("Gestionnaire", [role.name for role in await CompanyService().get_user_company_roles("legacy-member", "legacy-company")])
            operator = await session.scalar(select(UserCompanyRoleModel).where(
                UserCompanyRoleModel.company_id == "legacy-company", UserCompanyRoleModel.name == "Opérateur",
            ))
            owner_assignment = await session.scalar(select(UserCompanyRoleAssignmentModel).where(
                UserCompanyRoleAssignmentModel.company_id == "legacy-company",
                UserCompanyRoleAssignmentModel.user_id == "legacy-admin",
            ))
            owner_assignment.role_id = operator.id
            await session.commit()
            self.assertTrue((await migration.get_migration_status())["migration_needed"])
            self.assertEqual((await migration.migrate_company_member_roles())["migrated_members"], 1)
            self.assertFalse((await migration.get_migration_status())["migration_needed"])

    async def test_role_migration_on_fresh_schema(self):
        async with local_async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with LocalAsyncSession() as session:
            set_db_session(session)
            session.add(User(id="new-user", name="New", email="new-user@example.com", hashed_password="unused"))
            await session.commit()
            migration = MigrationService()
            self.assertEqual((await migration.get_migration_status())["old_system"]["users_with_old_roles"], 0)
            self.assertEqual((await migration.migrate_user_roles())["migrated_users"], 1)
            self.assertFalse((await migration.get_migration_status())["migration_needed"])
            created_id = await UserService().create_user({
                "name": "After signup", "email": "after-signup@example.com", "hashed_password": "unused",
            })
            self.assertIn("Regular User", [role.name for role in await UserService().get_user_roles(created_id)])
            self.assertFalse((await migration.get_migration_status())["migration_needed"])

    async def test_startup_migrates_legacy_administrator(self):
        async with local_async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(30)"))
        async with LocalAsyncSession() as session:
            session.add(User(id="startup-admin", name="Admin", email="startup-admin@example.com", hashed_password="unused"))
            await session.commit()
            await session.execute(text("UPDATE users SET role = 'admin' WHERE id = 'startup-admin'"))
            await session.commit()

        from app.main import startup_event
        await startup_event()
        async with LocalAsyncSession() as session:
            set_db_session(session)
            roles = await UserService().get_user_roles("startup-admin")
            self.assertIn("Platform Administrator", [role.name for role in roles])
            self.assertFalse((await MigrationService().get_migration_status())["migration_needed"])

    async def test_leave_request_round_trip_and_company_scope(self):
        async with local_async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with LocalAsyncSession() as session:
            set_db_session(session)
            session.add_all([
                User(id="leave-owner", name="Owner", email="leave-owner@example.com", hashed_password="unused"),
                Company(id="leave-company", name="Leave Company", owner_id="leave-owner"),
                Company(id="other-company", name="Other", owner_id="leave-owner"),
                EmployeeModel(id="leave-employee", company_id="leave-company", first_name="Awa", last_name="Sene"),
                EmployeeModel(id="other-employee", company_id="other-company", first_name="Bad", last_name="Scope"),
            ])
            await session.commit()

            leaves = EmployeeService()
            payload = EmployeeLeaveRequestCreate.model_validate({
                "employeeId": "leave-employee", "leaveType": "annual", "status": "pending",
                "startDate": "2026-10-08T00:00:00.000Z", "endDate": "2026-10-10T00:00:00.000Z",
                "daysRequested": 3, "reason": "Vacances",
            })
            leave_id = await leaves.create_leave_request("leave-employee", "leave-company", payload)
            saved = await leaves.get_leave_request_by_id(leave_id, "leave-employee", "leave-company")
            self.assertEqual(saved.employee_name, "Awa Sene")
            self.assertEqual(saved.start_date, "2026-10-08")
            self.assertEqual(saved.end_date, "2026-10-10")
            self.assertLessEqual(len(saved.requested_date), 20)
            self.assertEqual(len(await leaves.get_all_leave_requests("leave-company")), 1)
            self.assertEqual(len(await leaves.get_leave_requests("leave-employee", "leave-company")), 1)
            self.assertEqual(await leaves.get_all_leave_requests("other-company"), [])
            self.assertIsNone(await leaves.get_leave_request_by_id(leave_id, "leave-employee", "other-company"))

            with self.assertRaises(HTTPException) as cross_company:
                await leaves.create_leave_request("other-employee", "leave-company", payload)
            self.assertEqual(cross_company.exception.status_code, 404)
            with self.assertRaises(HTTPException) as reversed_dates:
                await leaves.update_leave_request(leave_id, "leave-employee", "leave-company", EmployeeLeaveRequestUpdate(endDate="2026-10-07"))
            self.assertEqual(reversed_dates.exception.status_code, 422)
            self.assertTrue(await leaves.update_leave_request(leave_id, "leave-employee", "leave-company", EmployeeLeaveRequestUpdate(endDate="2026-10-11")))
            self.assertTrue(await leaves.approve_leave_request(leave_id, "leave-employee", "leave-company", approved_by="leave-owner"))
            approved = await leaves.get_leave_request_by_id(leave_id, "leave-employee", "leave-company")
            self.assertEqual(approved.status, "approved")
            self.assertEqual(approved.end_date, "2026-10-11")
            self.assertLessEqual(len(approved.approved_date), 20)

    async def test_quote_and_payroll_round_trip(self):
        async with local_async_engine.begin() as connection:
            # Simulate a deployed table from before the additive details migration.
            await connection.execute(text("CREATE TABLE purchase_orders (id VARCHAR(20) PRIMARY KEY, company_id VARCHAR(64), order_number VARCHAR(100) NOT NULL, supplier_id VARCHAR(64), status VARCHAR(20) NOT NULL, total_amount FLOAT NOT NULL, created_at DATETIME, updated_at DATETIME)"))
            await connection.execute(text("CREATE TABLE suppliers (id VARCHAR(20) PRIMARY KEY, company_id VARCHAR(64), name VARCHAR(255) NOT NULL, email VARCHAR(255), phone VARCHAR(20), address TEXT, is_active BOOLEAN, created_at DATETIME, updated_at DATETIME)"))
            await connection.run_sync(Base.metadata.create_all)
            await _apply_non_destructive_alters(connection, dialect="sqlite")
            await _apply_non_destructive_alters(connection, dialect="sqlite")
            columns = await connection.execute(text("PRAGMA table_info(purchase_orders)"))
            self.assertIn("details", {column[1] for column in columns})
            columns = await connection.execute(text("PRAGMA table_info(suppliers)"))
            self.assertIn("details", {column[1] for column in columns})

        async with LocalAsyncSession() as session:
            set_db_session(session)
            session.add_all([
                User(id="test-user", name="Tester", email="tester@example.com", hashed_password="unused"),
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

            supplier_service = SupplierService()
            supplier_id = await supplier_service.create_supplier("test-company", SupplierCreate.model_validate({
                "name": "Fournisseur test", "contactPerson": "Fatou", "paymentTerms": "net_15",
                "currency": "XOF", "city": "Dakar", "notes": "Livraison rapide",
            }))
            supplier = await supplier_service.get_supplier_by_id(supplier_id, "test-company")
            self.assertIsInstance(supplier, Supplier)
            self.assertEqual(supplier.contact_person, "Fatou")
            self.assertEqual(supplier.payment_terms, "net_15")
            self.assertTrue(supplier.supplier_code.startswith("SUP-"))
            await supplier_service.update_supplier(supplier_id, "test-company", SupplierUpdate(city="Thiès", isActive=False))
            self.assertEqual((await supplier_service.get_supplier_by_id(supplier_id, "test-company")).city, "Thiès")
            self.assertFalse((await supplier_service.get_all_suppliers("test-company"))[0].is_active)
            self.assertIsNone(await supplier_service.get_supplier_by_id(supplier_id, "other-company"))

            session.add(TvaRateModel(id="test-rate", company_id="test-company", name="TVA", rate=18, is_default=True, is_active=True))
            await session.commit()
            company = await update_company_settings(
                "test-company",
                CompanySettings.model_validate({"tva": {"enabled": True, "defaultRateId": "test-rate"},
                    "stockAlertThreshold": 5, "allowPriceModification": False}),
                session,
                SimpleNamespace(id="test-user", email="tester@example.com", name="Tester"),
            )
            self.assertEqual(company.settings["tva"]["defaultRateId"], "test-rate")
            self.assertEqual(company.settings["stockAlertThreshold"], 5)

            owner = SimpleNamespace(id="test-user", platform_permissions=[])
            outsider = SimpleNamespace(id="outsider", platform_permissions=[])
            member = SimpleNamespace(id="test-member", platform_permissions=[])
            await ensure_company_access("test-company", owner, session, owner_only=True)
            with self.assertRaises(HTTPException) as denied:
                await ensure_company_access("test-company", outsider, session)
            self.assertEqual(denied.exception.status_code, 403)
            request = Request({"type": "http", "headers": [(b"cookie", b"companyId=test-company")]})
            with self.assertRaises(HTTPException) as denied:
                await get_company_id(request, "test-company", session, outsider)
            self.assertEqual(denied.exception.status_code, 403)
            stale_cookie_request = Request({"type": "http", "headers": [(b"cookie", b"companyId=old-company")]})
            self.assertEqual(await get_company_id(stale_cookie_request, "test-company", session, owner), "test-company")

            session.add_all([
                User(id="test-member", name="Member", email="member@example.com", hashed_password="unused"),
                CompanyMemberModel(id="test-membership", company_id="test-company", user_id="test-member", is_active=True),
            ])
            await session.commit()
            await ensure_company_access("test-company", member, session)
            with self.assertRaises(HTTPException) as denied:
                await ensure_company_access("test-company", member, session, owner_only=True)
            self.assertEqual(denied.exception.status_code, 403)

            session.add_all([
                Company(id="other-company", name="Other Company", owner_id="test-user"),
                UserCompanyRoleModel(id="test-role", company_id="test-company", name="Gestionnaire", permissions=["sales.read"]),
                UserCompanyRoleModel(id="foreign-role", company_id="other-company", name="Foreign", permissions=["company.users.manage"]),
            ])
            await session.commit()
            company_service = CompanyService()
            self.assertEqual({company.id for company in await company_service.get_all_companies()}, {"test-company", "other-company"})
            self.assertEqual((await company_service.update_company_plan("test-company", "basic")).subscription["plan"], "basic")
            self.assertIn("accessEndDate", (await company_service.cancel_company_subscription("test-company")).subscription)
            with self.assertRaises(HTTPException) as denied:
                await company_service.assign_company_role_to_user("test-member", "test-company", "foreign-role", "test-user")
            self.assertEqual(denied.exception.status_code, 404)
            with self.assertRaises(HTTPException) as denied:
                await company_service.assign_company_role_to_user("outsider", "test-company", "test-role", "test-user")
            self.assertEqual(denied.exception.status_code, 403)
            await company_service.assign_company_role_to_user("test-member", "test-company", "test-role", "test-user")
            self.assertEqual([role.id for role in await company_service.get_user_company_roles("test-member", "test-company")], ["test-role"])
            await company_service.set_company_member_role("test-company", "test-member", "test-role", "test-user")
            self.assertEqual([role.id for role in await company_service.get_user_company_roles("test-member", "test-company")], ["test-role"])
            member_list = await company_service.get_company_users("test-company")
            self.assertEqual(next(user for user in member_list if user.id == "test-member").company_roles, ["Gestionnaire"])
            with self.assertRaises(HTTPException) as denied:
                await company_service.set_company_member_role("test-company", "test-member", "foreign-role", "test-user")
            self.assertEqual(denied.exception.status_code, 404)
            with self.assertRaises(HTTPException) as denied:
                await company_service.set_company_member_role("test-company", "test-user", "test-role", "test-user")
            self.assertEqual(denied.exception.status_code, 400)

            with patch.dict(os.environ, {
                "AWS_BUCKET_NAME": "test-bucket", "AWS_REGION": "eu-west-1",
                "AWS_ACCESS_KEY_ID": "test-access", "AWS_SECRET_ACCESS_KEY": "test-secret",
            }):
                storage = UploadService()
                self.assertEqual(storage.s3_bucket_name, "test-bucket")
                self.assertEqual(storage.s3_region, "eu-west-1")
                self.assertEqual(storage.s3_access_key, "test-access")
                self.assertEqual(storage.s3_secret_key, "test-secret")

            file_service = FileService()
            with tempfile.TemporaryDirectory(prefix="senatrack-file-test-") as temp_files:
                file_service.local_files_path = Path(temp_files)
                def logo():
                    return UploadFile(file=io.BytesIO(b"\xff\xd8test-image"), filename="logo.jpg", headers=Headers({"content-type": "image/jpeg"}))

                first = await file_service.save_file(logo(), "company", "test-company", "logo_url", "test-company")
                second = await file_service.save_file(logo(), "company", "test-company", "logo_url", "other-company")
                self.assertNotEqual(first["file_id"], second["file_id"])
                self.assertEqual(len(await file_service.get_entity_files("company", "test-company", "test-company")), 1)
                self.assertEqual(len(await file_service.get_entity_files("company", "test-company", "other-company")), 1)
                self.assertFalse(await file_service.delete_file(first["file_id"], "other-company"))
                self.assertTrue(await file_service.delete_file(first["file_id"], "test-company"))
                with self.assertRaises(HTTPException) as denied:
                    await file_service.save_file(logo(), "../company", "test-company", "logo_url", "test-company")
                self.assertEqual(denied.exception.status_code, 400)

            key_service = ActivationKeyService()
            key = await key_service.create_activation_key(ActivationKeyCreate(plan="premium", duration=30, createdBy="test-user"))
            redemption = await key_service.use_activation_key(key.key, "test-company", "test-user")
            self.assertTrue(ActivationKeyUsageResponse.model_validate(redemption).success)
            self.assertFalse((await key_service.use_activation_key(key.key, "other-company", "test-user"))["success"])
            await session.refresh(await session.get(Company, "test-company"))
            self.assertEqual((await session.get(Company, "test-company")).subscription["plan"], "premium")

            session.add(User(id="invitee", name="Invitee", email="invitee@example.com", hashed_password="unused"))
            await session.commit()
            invitation_service = InvitationService()
            invitation = await create_invitation_route(CompanyInvitationCreate(
                companyId="test-company", email="invitee@example.com", role="operator", invitedBy="outsider",
            ), session, SimpleNamespace(id="test-user", email="tester@example.com", name="Tester", platform_permissions=[]))
            self.assertEqual(invitation.invited_by, "test-user")
            self.assertEqual(CompanyInvitationSchema.model_validate(invitation).email, "invitee@example.com")
            with self.assertRaises(HTTPException) as denied:
                await pending_invitations_route("invitee@example.com", session, SimpleNamespace(email="wrong@example.com"))
            self.assertEqual(denied.exception.status_code, 403)
            with self.assertRaises(HTTPException) as denied:
                await invitation_service.accept_invitation(invitation.token, "invitee", "wrong@example.invalid")
            self.assertEqual(denied.exception.status_code, 403)
            accepted = await invitation_service.accept_invitation(invitation.token, "invitee", "invitee@example.com")
            self.assertTrue(accepted.success)
            await ensure_company_access("test-company", SimpleNamespace(id="invitee", platform_permissions=[]), session)
            self.assertEqual([role.name for role in await company_service.get_user_company_roles("invitee", "test-company")], ["Opérateur"])

            user_service = UserService()
            admin = await user_service.set_platform_role("test-user", "Platform Administrator", "test-user")
            self.assertIn("admin.access", admin.platform_permissions)
            member_user = await user_service.set_platform_role("test-member", "Regular User", "test-user")
            self.assertEqual(member_user.platform_roles, ["Regular User"])
            with self.assertRaises(HTTPException) as denied:
                await update_user("test-member", UserUpdate(currentCompanyId="other-company"), session, member_user)
            self.assertEqual(denied.exception.status_code, 403)
            inactive = await user_service.set_user_active("test-member", False)
            self.assertFalse(inactive.is_active)
            self.assertFalse(next(user for user in await company_service.get_company_users("test-company") if user.id == "test-member").is_active)
            self.assertIsNone(await user_service.get_user_by_id("test-member"))
            self.assertFalse((await user_service.get_user_by_id("test-member", include_inactive=True)).is_active)
            self.assertIn("test-member", {user.id for user in await user_service.get_all_users()})
            self.assertTrue((await user_service.set_user_active("test-member", True)).is_active)
            self.assertEqual((await user_service.get_user_stats())["total"], 3)
            with self.assertRaises(HTTPException) as denied:
                await update_user_as_admin("test-member", UserAdminUpdate(name="Member", email="tester@example.com"), session, admin)
            self.assertEqual(denied.exception.status_code, 409)
            renamed = await update_user_as_admin("test-member", UserAdminUpdate(name="New Member", email="newmember@example.com"), session, admin)
            self.assertEqual(renamed.name, "New Member")
            with self.assertRaises(HTTPException) as denied:
                await update_user_status("test-user", UserStatusUpdate(isActive=False), admin)
            self.assertEqual(denied.exception.status_code, 400)
            with self.assertRaises(HTTPException) as denied:
                await update_user_platform_role("test-user", UserPlatformRoleUpdate(roleName="Regular User"), admin)
            self.assertEqual(denied.exception.status_code, 400)
            await user_service.update_user("test-member", {"current_company_id": "other-company"})
            auth_service = AuthService()
            token = auth_service.create_access_token({"user_id": "test-member", "email": "newmember@example.com"})
            current_member = await auth_service.get_current_user(token)
            self.assertIsNone(current_member.current_company_id)
            profile = await auth_service.get_user_profile(current_member, token)
            self.assertEqual(profile.current_company_id, "test-company")

if __name__ == "__main__":
    unittest.main()
