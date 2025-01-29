# Use an official Node.js image
FROM node:16

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json for dependency installation
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy the entire frontend code to the container
COPY . .

# Expose the frontend port
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]
