#define MyAppName "Cashbox client"
#define AtolDriverX86 "KKT10-10.10.0.0-windows32-setup.exe"
#define AtolDriverX64 "KKT10-10.10.0.0-windows64-setup.exe"

[Setup]
AppName={#MyAppName}
AppVersion=1.0
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=cashbox_client_installer
OutputDir=.build/installer
Compression=lzma
SolidCompression=yes
SetupIconFile=static\icon.ico

[Files]
; Копируем все файлы из папки dist в папку установки
Source: ".build\dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "static\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Копируем установщики для x86 и x64 драйверов
Source: "drivers\{#AtolDriverX86}"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "drivers\{#AtolDriverX64}"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
; Ярлык в меню "Пуск"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppName}.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
; Ярлык на рабочем столе
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppName}.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"

[Run]
; Запуск основного .exe файла после установки
Filename: "{app}\{#MyAppName}.exe"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InstallDriver;
var
  ResultCode: Integer;
  DriverPath: String;
begin
  { Проверяем, является ли операционная система 64-битной }
  if IsWin64 then
  begin
    { Устанавливаем путь к драйверу x64 в временной директории }
    DriverPath := ExpandConstant('{tmp}\{#AtolDriverX64}');
  end
  else
  begin
    { Устанавливаем путь к драйверу x86 в временной директории }
    DriverPath := ExpandConstant('{tmp}\{#AtolDriverX86}');
  end;

  { Запускаем установку драйвера }
  if not Exec(DriverPath, '', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('Установка драйвера не удалась! ' + SysErrorMessage(ResultCode), mbError, MB_OK);
    { Прерываем установку, если драйвер не удалось установить }
    Abort();
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    InstallDriver();
  end;
end;