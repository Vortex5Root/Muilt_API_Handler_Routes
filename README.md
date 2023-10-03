# Muilt_API_Handler_Routes

- This Libs add Tables to Redis and Routes to Handler the same Tables
## install with Poetry

```bash
poetry add https://github.com/Vortex5Root/Muilt_API_Handler_Routes.git
```

# Usage

```python
from fastapi import FastAPI

from muilt_api_handler_routes.Routes.Configs  import ConfigsModel
from muilt_api_handler_routes.Routes.Skeleton import Skeleton

app = FastAPI()

app.include_router(ConfigModel(),  prefix="/v1/muiltapi")
app.include_router(Skeletons(),    prefix="/v1/muiltapi")
```


## Conclusion
The Library is used to manage multiple APIs, as well as routing logic for directing requests to the appropriate endpoints.

## License
[![MIT](icons/license40.png)](https://choosealicense.com/licenses/mit/)
