# Use the official Node.js 20 image (Debian based)
FROM node:20

# Install dependencies required by Playwright (Chromium) and Cloudflare WARP
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libcomposite1 \
    libasound2 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY bot/package*.json ./

# Install Node.js dependencies
RUN npm install

# Install Playwright browsers (Chromium only to save space)
RUN npx playwright install chromium
RUN npx playwright install-deps chromium

# Copy the rest of the application code
COPY bot/ ./

# Expose the port the Express server will run on (Hugging Face standard is 7860)
EXPOSE 7860

# Command to run the application (Uses ts-node in development or compiled js in production)
CMD ["npx", "ts-node", "src/index.ts"]
