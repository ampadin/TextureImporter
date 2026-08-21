from enum import Enum, auto

class TextureType(Enum):
    UNKNOWN = auto()
    BASECOLOR = auto()
    NORMAL = auto()
    ORM = auto()
    AO = auto()
    ROUGHNESS = auto()
    METALLIC = auto()
    HEIGHT = auto()
    OPACITY = auto()
    EMISSIVE = auto()


class CompressionType(Enum):
    DEFAULT = auto()
    NORMAL = auto()
    MASK = auto()
    DISPLACEMENT = auto()
    GRAYSCALE = auto()


TEXTURE_SETTINGS =  {
    TextureType.BASECOLOR:{ 
        "srgb": True,
        "compression": CompressionType.DEFAULT
    },
    TextureType.NORMAL:{ 
        "srgb": False,
        "compression": CompressionType.NORMAL 
    },
    TextureType.ORM:{ 
        "srgb": False,
        "compression": CompressionType.MASK 
    },
    TextureType.HEIGHT:{ 
        "srgb": False,
        "compression": CompressionType.DISPLACEMENT 
    },
    TextureType.OPACITY:{ 
        "srgb": False,
        "compression": CompressionType.MASK 
    },
    TextureType.EMISSIVE:{ 
        "srgb": True,
        "compression": CompressionType.DEFAULT 
    },  
    TextureType.ROUGHNESS:{ 
        "srgb": False,
        "compression": CompressionType.GRAYSCALE 
    },
    TextureType.AO:{ 
        "srgb": False,
        "compression": CompressionType.GRAYSCALE 
    },
    TextureType.METALLIC:{ 
        "srgb": False,
        "compression": CompressionType.GRAYSCALE 
    },
}

class JobStatus(Enum):
    WAITING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()