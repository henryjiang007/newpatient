# SFDS microservice.py [![CircleCI](https://badgen.net/circleci/github/SFDigitalServices/pdf-generator/main)](https://circleci.com/gh/SFDigitalServices/pdf-generator) [![Coverage Status](https://coveralls.io/repos/github/SFDigitalServices/pdf-generator/badge.svg?branch=main)](https://coveralls.io/github/SFDigitalServices/pdf-generator?branch=main)
SFDS PDF Generator allows other applications to create PDF files based on a template.

## Starter guide
Please see 
([SFDS microservice boiler template](https://github.com/SFDigitalServices/microservice-py)

## Get started
The PDF Generator expects 2 parameters: 
* Form data in ([JSON])(https://www.json.org/json-en.html) format
* A PDF template which form fields that matches the keys in the form

It returns a PDF object as python bytes

### Calling the microservice
Make a HTTP POST to the deployed URL with
    HTTP header of ACCESS_KEY and TEMPLATE_FILE(see sample.pdf)
    Form data, see sample-data.json

