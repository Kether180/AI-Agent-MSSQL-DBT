#!/bin/sh
# Start nginx in background
nginx &
# Start backend server
exec ./server
