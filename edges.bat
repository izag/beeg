@echo off

FOR /L %%a IN (81,1,352) DO (
	ping -n 1 -w 1000 edge%%a.stream.highwebmedia.com >nul && (echo %%a)
)
 
