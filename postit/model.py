import random
import uuid


class TodoItem:
    def __init__(self, text="", done=False, item_id=None):
        self.id = item_id or str(uuid.uuid4())
        self.text = text
        self.done = done

    def to_dict(self):
        return {"id": self.id, "text": self.text, "done": self.done}

    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d.get("text", ""),
            done=bool(d.get("done", False)),
            item_id=d.get("id"),
        )


class Note:
    def __init__(self, note_type="text"):
        self.id = str(uuid.uuid4())
        self.type = note_type  # 'text' | 'todo'
        self.title = ""
        self.content = ""
        self.items = []
        self.color = "yellow"
        self.x = None
        self.y = None
        self.w = 250
        self.h = 300
        self.rotation = round(random.uniform(-2.2, 2.2), 2)
        self.always_on_top = False
        self.font_size = 13
        self.visible = True

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "items": [i.to_dict() for i in self.items],
            "color": self.color,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "rotation": self.rotation,
            "always_on_top": self.always_on_top,
            "font_size": self.font_size,
            "visible": self.visible,
        }

    @classmethod
    def from_dict(cls, d):
        n = cls()
        n.id = d.get("id", n.id)
        n.type = d.get("type", "text")
        n.title = d.get("title", "")
        n.content = d.get("content", "")
        n.items = [TodoItem.from_dict(i) for i in d.get("items", [])]
        n.color = d.get("color", "yellow")
        n.x = d.get("x")
        n.y = d.get("y")
        n.w = int(d.get("w", 250))
        n.h = int(d.get("h", 300))
        n.rotation = float(d.get("rotation", 0.0))
        n.always_on_top = bool(d.get("always_on_top", False))
        n.font_size = int(d.get("font_size", 13))
        n.visible = bool(d.get("visible", True))
        return n
