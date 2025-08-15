#!/bin/bash

# Development script for Carac project
# Run with: ./scripts/dev.sh

set -e

COMMAND=${1:-help}
TARGET=${2:-}

show_help() {
    echo "Carac Development Script"
    echo "========================"
    echo ""
    echo "Usage: ./scripts/dev.sh <command> [target]"
    echo ""
    echo "Commands:"
    echo "  install     - Install dependencies with Poetry"
    echo "  run         - Run the application"
    echo "  test        - Run tests"
    echo "  lint        - Run linting checks"
    echo "  format      - Format code"
    echo "  typecheck   - Run type checking"
    echo "  build       - Build executable with PyInstaller"
    echo "  clean       - Clean build artifacts"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/dev.sh install"
    echo "  ./scripts/dev.sh run"
    echo "  ./scripts/dev.sh test"
    echo "  ./scripts/dev.sh build"
}

install_dependencies() {
    echo "Installing dependencies..."
    poetry install --with dev,packaging
    if [ $? -eq 0 ]; then
        echo "Dependencies installed successfully!"
    else
        echo "Failed to install dependencies!"
        exit 1
    fi
}

run_application() {
    echo "Running Carac application..."
    poetry run carac
}

run_tests() {
    echo "Running tests..."
    if [ -n "$TARGET" ]; then
        poetry run pytest "$TARGET"
    else
        poetry run pytest
    fi
}

run_linting() {
    echo "Running linting checks..."
    poetry run ruff check src/
    if [ $? -eq 0 ]; then
        echo "Linting passed!"
    else
        echo "Linting failed!"
        exit 1
    fi
}

format_code() {
    echo "Formatting code..."
    poetry run ruff format src/
    if [ $? -eq 0 ]; then
        echo "Code formatted successfully!"
    else
        echo "Code formatting failed!"
        exit 1
    fi
}

run_typecheck() {
    echo "Running type checking..."
    poetry run mypy src/carac
    if [ $? -eq 0 ]; then
        echo "Type checking passed!"
    else
        echo "Type checking failed!"
        exit 1
    fi
}

build_executable() {
    echo "Building executable..."
    poetry run pyinstaller packaging/pyinstaller/carac.spec
    if [ $? -eq 0 ]; then
        echo "Executable built successfully!"
        echo "Location: dist/carac"
    else
        echo "Build failed!"
        exit 1
    fi
}

clean_build() {
    echo "Cleaning build artifacts..."
    if [ -d "dist" ]; then
        rm -rf dist
        echo "Removed dist/ directory"
    fi
    if [ -d "build" ]; then
        rm -rf build
        echo "Removed build/ directory"
    fi
    if ls *.spec 1> /dev/null 2>&1; then
        rm *.spec
        echo "Removed .spec files"
    fi
    echo "Clean completed!"
}

# Main script logic
case $COMMAND in
    install)
        install_dependencies
        ;;
    run)
        run_application
        ;;
    test)
        run_tests
        ;;
    lint)
        run_linting
        ;;
    format)
        format_code
        ;;
    typecheck)
        run_typecheck
        ;;
    build)
        build_executable
        ;;
    clean)
        clean_build
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './scripts/dev.sh help' for usage information"
        exit 1
        ;;
esac
