from __future__ import annotations
import asyncio
import uuid


# This Class can be used to make existing ST Api Async.
class FutureWithId(asyncio.Future):
    map: dict[str, asyncio.Future] = {}

    def __init__(self, id: str|None=None):
        super().__init__()
        self.id = id or str(uuid.uuid4())
        FutureWithId.map[self.id] = self

        def clear(_):
            if self.id in FutureWithId.map:
                FutureWithId.map.pop(self.id)

        self.add_done_callback(clear)

    @staticmethod
    def get(future_id: str):
        if future_id not in FutureWithId.map:
            return
        return FutureWithId.map.pop(future_id)




