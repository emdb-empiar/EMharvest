FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the entire emharvest project into the container
COPY . /app/emharvest

# Install dependencies
RUN pip install --no-cache-dir -r /app/emharvest/requirements.txt

# Set the working directory inside emharvest
WORKDIR /app/emharvest

# Allow dynamic arguments for execution
ENTRYPOINT ["python", "emh.py"]



