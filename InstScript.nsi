 !include MUI2.nsh
 RequestExecutionLevel admin
 Name "Кассовый клиент"
 OutFile cashbox_client_installer.exe
 InstallDir "$APPDATA\cashbox_client"
 !define STARTMENUGROUP "Кассовый клиент"
 !define MUI_ICON "D:\projects\cashbox_client\icon_tk.ico"
 !define MUI_WELCOMEPAGE_TITLE "Программа установки кассового клиента"
 !define MUI_FINISHPAGE_TITLE "Завершение установки"
 !insertmacro MUI_PAGE_WELCOME
 !insertmacro MUI_PAGE_DIRECTORY
 !insertmacro MUI_PAGE_COMPONENTS
 !insertmacro MUI_PAGE_INSTFILES
 !insertmacro MUI_PAGE_FINISH
 !insertmacro MUI_LANGUAGE "Russian"
 
 
 

 Section "Кассовый клиент"
   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "Кассовый клиент" '"$INSTDIR\cashbox_client.exe"'
    SetOutPath $INSTDIR
   File /r "D:\projects\cashbox_client\dist\cashbox_client\"

 SectionEnd
 
 
 Section "Драйвер АТОЛ 10.10 x86"
   SetOutPath $INSTDIR\Temp
   File  "D:\projects\cashbox_client\atol_drivers_installer\KKT10-10.10.0.0-windows32-setup.exe"
   ExecWait "$INSTDIR\Temp\KKT10-10.10.0.0-windows32-setup.exe"
   RMDir   /r "$INSTDIR\Temp"
 SectionEnd

  Section "Драйвер АТОЛ 10.10 x64"
   SetOutPath $INSTDIR\Temp
   File  "D:\projects\cashbox_client\atol_drivers_installer\KKT10-10.10.0.0-windows64-setup.exe"
   ExecWait "$INSTDIR\Temp\KKT10-10.10.0.0-windows64-setup.exe"
   RMDir   /r "$INSTDIR\Temp"
 SectionEnd

 SectionGroup "Создать ярлыки"
  Section "в меню Пуск"
    SetShellVarContext all
    SetOutPath $INSTDIR
    CreateShortCut "$SMPROGRAMS\Кассовый клиент.lnk" "$INSTDIR\cashbox_client.exe"
  SectionEnd
  Section "на Рабочем столе"
    SetShellVarContext all
    SetOutPath $INSTDIR
    CreateShortCut "$DESKTOP\Кассовый клиент.lnk" "$INSTDIR\cashbox_client.exe"
  SectionEnd
SectionGroupEnd 