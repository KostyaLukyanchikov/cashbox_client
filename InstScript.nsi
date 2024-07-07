 !include MUI2.nsh
 RequestExecutionLevel admin
 Name "�������� ������"
 OutFile cashbox_client_installer.exe
 InstallDir "$APPDATA\cashbox_client"
 !define STARTMENUGROUP "�������� ������"
 !define MUI_ICON "D:\projects\cashbox_client\icon_tk.ico"
 !define MUI_WELCOMEPAGE_TITLE "��������� ��������� ��������� �������"
 !define MUI_FINISHPAGE_TITLE "���������� ���������"
 !insertmacro MUI_PAGE_WELCOME
 !insertmacro MUI_PAGE_DIRECTORY
 !insertmacro MUI_PAGE_COMPONENTS
 !insertmacro MUI_PAGE_INSTFILES
 !insertmacro MUI_PAGE_FINISH
 !insertmacro MUI_LANGUAGE "Russian"
 
 
 

 Section "�������� ������"
   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "�������� ������" '"$INSTDIR\cashbox_client.exe"'
    SetOutPath $INSTDIR
   File /r "D:\projects\cashbox_client\dist\cashbox_client\"

 SectionEnd
 
 
 Section "������� ���� 10.10 x86"
   SetOutPath $INSTDIR\Temp
   File  "D:\projects\cashbox_client\atol_drivers_installer\KKT10-10.10.0.0-windows32-setup.exe"
   ExecWait "$INSTDIR\Temp\KKT10-10.10.0.0-windows32-setup.exe"
   RMDir   /r "$INSTDIR\Temp"
 SectionEnd

  Section "������� ���� 10.10 x64"
   SetOutPath $INSTDIR\Temp
   File  "D:\projects\cashbox_client\atol_drivers_installer\KKT10-10.10.0.0-windows64-setup.exe"
   ExecWait "$INSTDIR\Temp\KKT10-10.10.0.0-windows64-setup.exe"
   RMDir   /r "$INSTDIR\Temp"
 SectionEnd

 SectionGroup "������� ������"
  Section "� ���� ����"
    SetShellVarContext all
    SetOutPath $INSTDIR
    CreateShortCut "$SMPROGRAMS\�������� ������.lnk" "$INSTDIR\cashbox_client.exe"
  SectionEnd
  Section "�� ������� �����"
    SetShellVarContext all
    SetOutPath $INSTDIR
    CreateShortCut "$DESKTOP\�������� ������.lnk" "$INSTDIR\cashbox_client.exe"
  SectionEnd
SectionGroupEnd 