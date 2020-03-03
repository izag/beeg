for /l %%x in (1, 1, 10) do (
	"c:\Program Files (x86)\GnuWin32\bin\wget.exe" https://chaturbate.com/?page=%%x  --no-check-certificate -e use_proxy=no -e https_proxy=151.253.165.70:8080 -O %%x.htm --user-agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0"
)