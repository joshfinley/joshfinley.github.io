# Start from the official Go 1.20 image
FROM golang:1.20-alpine AS builder

# Install git and necessary build tools
RUN apk add --no-cache git make

# Set the working directory
WORKDIR /src

# Clone a specific version of Hugo compatible with Go 1.20
RUN git clone -b v0.111.3 https://github.com/gohugoio/hugo.git .

# Build Hugo
RUN go build -o /go/bin/hugo

# Start a new stage from a smaller base image
FROM alpine:latest

# Copy the Hugo binary from the builder stage
COPY --from=builder /go/bin/hugo /usr/local/bin/hugo

# Set the working directory to /site
WORKDIR /site

# Expose the default Hugo port
EXPOSE 1313

# Set the entrypoint to Hugo
ENTRYPOINT ["hugo"]

# The default command is empty, allowing us to pass commands when running the container
CMD []