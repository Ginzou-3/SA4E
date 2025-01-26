# Use an OpenJDK base image
FROM eclipse-temurin:17-jdk-alpine

# Create app directory
WORKDIR /app

# Copy your Spring Boot fat JAR into the container
COPY target/xmaswishes-1.0.0-SNAPSHOT.jar /app/xmaswishes.jar

# Copy the root cert into the image
COPY root.crt /app/cc-ca.crt

# Expose port 8080
EXPOSE 8080

# Run the Spring Boot app
ENTRYPOINT ["java","-jar","/app/xmaswishes.jar"]