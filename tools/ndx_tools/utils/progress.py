import warnings

from loguru import logger
from rich.console import Console
from rich.text import Text
from tqdm import TqdmExperimentalWarning

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

__console = Console(stderr=True)
logger.configure(
    handlers=[
        {
            "sink": lambda s: __console.print(Text.from_ansi(s)),
            "colorize": __console.is_terminal,
        }
    ]
)

# files = ["foo.bin", "bar.bin"]
# pb = tqdm(range(0x100), unit="B", unit_divisor=1024, unit_scale=True, options={"console": __console})
# for i in pb:
#     pb.update(i)
#     pb.set_description(f"setting {i}")
#     time.sleep(0.5)
