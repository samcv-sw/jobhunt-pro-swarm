import inspect

import starlette
from starlette.middleware.cors import CORSMiddleware

print("Starlette version:", starlette.__version__)
print(inspect.getsource(CORSMiddleware.is_allowed_origin))
