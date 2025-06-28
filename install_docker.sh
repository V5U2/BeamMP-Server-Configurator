#!/bin/bash

echo "Installing Docker Python module for BeamMP Server Configurator..."
echo

# Try different pip commands
echo "Attempting to install docker module..."

# Try python -m pip first
if python -m pip install docker==6.1.3; then
    echo
    echo "Successfully installed Docker module!"
    echo "You can now use the server management features."
    exit 0
fi

# Try pip directly
if pip install docker==6.1.3; then
    echo
    echo "Successfully installed Docker module!"
    echo "You can now use the server management features."
    exit 0
fi

# Try pip3
if pip3 install docker==6.1.3; then
    echo
    echo "Successfully installed Docker module!"
    echo "You can now use the server management features."
    exit 0
fi

echo
echo "Failed to install Docker module automatically."
echo
echo "Please try one of the following manual methods:"
echo
echo "1. Using python -m pip:"
echo "   python -m pip install docker==6.1.3"
echo
echo "2. Using pip directly:"
echo "   pip install docker==6.1.3"
echo
echo "3. Using pip3:"
echo "   pip3 install docker==6.1.3"
echo
echo "4. If you're using a virtual environment:"
echo "   source venv/bin/activate"
echo "   pip install docker==6.1.3"
echo
echo "Note: The configurator will still work without Docker module,"
echo "but server management features will be disabled."
echo 