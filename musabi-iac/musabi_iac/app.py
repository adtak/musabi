#!/usr/bin/env python3

import aws_cdk as cdk

from musabi_iac.musabi_stack import MusabiStack

app = cdk.App()
MusabiStack(app, "musabiStack")

app.synth()
