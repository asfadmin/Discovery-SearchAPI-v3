from mangum import Mangum
import uvicorn
from application.application import app

# Lambda handle:
lambda_handler = Mangum(app)

# Beanstalk handle:
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
