@set EMAIL="the_vortex01@hotmail.com"
@set PASSWORD="gdpfre87"
@set QUALITY="SQTest"
@set STREAM="both"
python ..\gomstreamer.py -e %EMAIL% -p %PASSWORD% -q %QUALITY% -s %STREAM% %*
