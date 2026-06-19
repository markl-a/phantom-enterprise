# mes_connector

Build status is tracked in [`../docs/phantom-enterprise.md`](../docs/phantom-enterprise.md) (the status source
of truth).

Target: 鴻海 / 南亞科 / 台積 in-house MES APIs. Schemas vary per fab and
are NDA-locked, so this module activates only after joining a target
company or signing an NDA-covered pilot.

Planned shape: ``list_lots()``, ``get_lot_status(lot_id)``, ``post_wafer_event(...)``.

Activates: M4 W13-14 (~2026-08) or first real MES customer, whichever first.
