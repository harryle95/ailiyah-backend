import random
from pathlib import Path
from uuid import UUID

from src.model import Request
from src.service.storage import StorageServer

__all__ = ("generate_output",)


ParentPath = Path(__file__).parents[0]
ResourcePath = ParentPath / "resource"

PROP_MAPPING = {
    ("dark", "grey"): ["dark_grey.jpg"],
    ("jacket"): ["jacket.png"],
    ("model", "outfit", "hat", "bag", "shoe"): ["model_outfit_hat_bag_shoe_v1.png", "model_outfit_hat_bag_shoe_v2.png"],
    ("sketch", "tree"): ["sketch_trees.jpg"],
    ("sunglasses"): ["sunglasses_face.png"],
    ("triangular", "windows"): ["triangular_windows.jpg"],
    ("white", "flower"): ["white_flower.jpg"],
    ("white", "top", "black", "skirt"): ["white_top_black_skirt_v1.png"],
    ("dog"): ["dog_v1.jpeg", "dog_v2.jpeg"],
    ("golden", "retriever"): ["golden-retriever.jpg"],
}


def get_output(text: str) -> str:
    for kwds, v in PROP_MAPPING.items():
        matching = True
        for kw in kwds:
            if kw not in text:
                matching = False
                break
        if matching:
            return random.choice(v)
    return "dog_v1.jpeg"


async def generate_output(request: Request, storage: StorageServer) -> UUID:
    if request.output_image is not None:
        await storage.delete(request.output_image)
    requests_texts = " ".join([prompt.text for prompt in request.prompts])
    with Path(ResourcePath / get_output(requests_texts)).open("rb") as file:
        return await storage.create(file.read())
