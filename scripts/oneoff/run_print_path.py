import os
for x in sorted(os.listdir('test_env/Lib/site-packages')):
    logger.debug(x.encode('ascii', errors='replace').decode('ascii'))
