#!/usr/bin/env python3

from aws_cdk import core

from src.musabi_stack import MusabiStack


app = core.App()
MusabiStack(app, "musabiStack")

app.synth()
