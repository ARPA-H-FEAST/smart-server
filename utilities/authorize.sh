#!/bin/bash

CODE_VERIFIER=VBE5SOAAHK44ZQ5985DR5D535JVVHAYFT4TEBXM846EBB71AWB4KNC1LWNIU980B82QVN7UNN82FHWFW
ID=rtF7yay2qtfADKHpnjRobidvYCaaB6XA132CfMKX
SECRET=Gwto0kTHr4lX0eL04ydHUWrP5ymWvYMb5okxXwkpe5ujHwdlTeYmhJku13kJGrP7fnSKAZCk0IXBrs29lPz33odminO2Vd5olCN8KGDFmpLLJUsbr5MB0N41XBOId8Dh
CODE=code

curl -vvv -X POST \
    -H "Cache-Control: no-cache" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    "http://localhost:8000/o/token/" \
    -d "client_id=${ID}" \
    -d "client_secret=${SECRET}" \
    -d "code=${CODE}" \
    -d "code_verifier=${CODE_VERIFIER}" \
    -d "redirect_uri=http://localhost:3000/callback" \
    -d "grant_type=authorization_code"
