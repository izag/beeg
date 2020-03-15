@Echo OFF

FOR /D /R %%# in (*) DO (
	PUSHD "%%#"
	copy /b *ts all.xts
	del *.ts
	move all.xts all.ts
	POPD
)