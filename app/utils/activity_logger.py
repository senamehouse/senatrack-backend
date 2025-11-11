from __future__ import annotations
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar, Union
import inspect
import functools

from app.services.activity_service import ActivityService
from app.schemas.activity_schema import ActivityLogCreate

T = TypeVar("T")
activity_service = ActivityService()


class ActivityActor:
    def __init__(self, user_id: Optional[str], user_email: Optional[str]):
        self.user_id = user_id
        self.user_email = user_email


async def log_activity(
    *,
    action: str,
    details: str,
    company_id: Optional[str],
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    actor: Optional[ActivityActor] = None,
) -> str:
    payload = ActivityLogCreate(
        action=action,
        details=details,
        userId=actor.user_id if actor else None,
        companyId=company_id,
        entityType=entity_type,
        entityId=entity_id,
        extraData=extra_data,
    )
    return await activity_service.create_activity_log(payload)


Extractor = Callable[[Any, tuple, dict], Any]


def _resolve(val: Union[str, Extractor, None], result: Any, args: tuple, kwargs: dict) -> Any:
    if callable(val):
        return val(result, args, kwargs)
    return val


def audit(
    *,
    action: str,
    entity_type: Optional[str] = None,
    details: Union[str, Extractor],
    entity_id: Union[str, Extractor, None] = None,
    company_id: Union[str, Extractor, None] = lambda _r, _a, kw: kw.get("company_id"),
    actor: Union[ActivityActor, Extractor, None] = lambda _r, _a, kw: kw.get("actor"),
    extra: Union[Dict[str, Any], Extractor, None] = None,
    on_error: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., Coroutine[Any, Any, T]]]:
    def decorator(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
        is_coro = inspect.iscoroutinefunction(func)
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            bound = sig.bind_partial(*args, **kwargs)
            kwn = dict(bound.arguments)
            try:
                result = await func(*args, **kwargs) if is_coro else func(*args, **kwargs)
            except Exception as e:
                if on_error:
                    try:
                        det = details(result=None, args=args, kwargs=kwn) if callable(details) else str(details).format(result=None, args=args, kwargs=kwn)
                        cid = _resolve(company_id, None, args, kwn)
                        act = _resolve(actor, None, args, kwn)
                        ext = _resolve(extra, None, args, kwn)
                        await log_activity(
                            action=f"{action}_ERROR",
                            details=det if det else f"{action} échec: {e}",
                            company_id=cid,
                            entity_type=entity_type,
                            entity_id=_resolve(entity_id, None, args, kwn),
                            extra_data={"error": str(e), **(ext or {})} if isinstance(ext, dict) else {"error": str(e)},
                            actor=act if isinstance(act, ActivityActor) else None,
                        )
                    except Exception:
                        pass
                raise

            try:
                det = details(result, args, kwn) if callable(details) else str(details).format(result=result, args=args, kwargs=kwn)
                cid = _resolve(company_id, result, args, kwn)
                ent_id = _resolve(entity_id, result, args, kwn)
                act = _resolve(actor, result, args, kwn)
                ext = _resolve(extra, result, args, kwn)
                await log_activity(
                    action=action,
                    details=det,
                    company_id=cid,
                    entity_type=entity_type,
                    entity_id=ent_id,
                    extra_data=ext if isinstance(ext, dict) else None,
                    actor=act if isinstance(act, ActivityActor) else None,
                )
            except Exception:
                pass

            return result

        return wrapper

    return decorator


