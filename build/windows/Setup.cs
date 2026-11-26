using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.Windows.Forms;
using System.Drawing;
using Microsoft.Win32;
[assembly: AssemblyTitle("FullArcCAD Setup")]
[assembly: AssemblyProduct("FullArcCAD")]
[assembly: AssemblyVersion("0.2.266.0")]
internal static class Setup {
    static List<Dictionary<string,object>> Extract(string root) {
        Directory.CreateDirectory(root);var files=new List<Dictionary<string,object>>();
        using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("FullArcCAD.Payload.zip"))
        using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)){
            foreach(var entry in zip.Entries){
                if(entry.FullName.EndsWith("/"))continue;
                string path=Common.SafePath(root,entry.FullName.Replace('/','\\'));Directory.CreateDirectory(Path.GetDirectoryName(path));
                using(var source=entry.Open())using(var output=new FileStream(path,FileMode.Create,FileAccess.Write))source.CopyTo(output);
                files.Add(new Dictionary<string,object>{{"path",entry.FullName},{"sha256",Common.Hash(path)}});
            }
        }
        Common.WriteJson(Path.Combine(root,"install-manifest.json"),new {productId=Common.ProductId,version=Common.Version,files=files});return files;
    }
    static void Install(string root,string engine,bool desktop) {
        if(Common.EngineAlive(Common.StateRoot))throw new IOException("FullArcCADを閉じてからインストールしてください。");
        Common.ValidateEngine(engine);
        string marker=Path.Combine(root,"install-manifest.json");
        if(Directory.Exists(root)&&Directory.EnumerateFileSystemEntries(root).Any()){
            if(!File.Exists(marker)||Convert.ToString(Common.ReadJson(marker)["productId"])!=Common.ProductId)throw new IOException("既存の別フォルダーへはインストールできません。");
        }
        var files=Extract(root);Common.WriteJson(Path.Combine(root,"launcher.json"),new {engine=engine});
        files.Add(new Dictionary<string,object>{{"path","launcher.json"},{"sha256",Common.Hash(Path.Combine(root,"launcher.json"))}});
        Common.WriteJson(marker,new {productId=Common.ProductId,version=Common.Version,files=files});
        Common.Register(root);
        Common.Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs),"FullArcCAD-Native","FullArcCAD-Native.lnk"),Path.Combine(root,"FullArcCAD.exe"));
        if(desktop)Common.Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),"FullArcCAD-Native.lnk"),Path.Combine(root,"FullArcCAD.exe"));
    }
    [STAThread]static int Main(string[] args) {
        Application.EnableVisualStyles();
        if(args.Length==2 && args[0]=="--install-silent"){
            try{string engine=Path.GetFullPath(args[1]);
                if(!File.Exists(engine)||!Path.GetFileName(engine).Equals("freecad.exe",StringComparison.OrdinalIgnoreCase))return 2;
                Install(Common.InstallRoot,engine,false);return 0;
            }catch(Exception e){File.WriteAllText(Path.Combine(Common.Base,"setup-error.txt"),e.ToString());return 1;}
        }

        try {
            if(args.Length==2&&args[0]=="--extract-only"){
                string root=Path.GetFullPath(args[1]);if(Directory.Exists(root)&&Directory.EnumerateFileSystemEntries(root).Any())throw new IOException("Extraction target must be empty");
                var files=Extract(root);Common.WriteJson(Path.Combine(root,"launcher.json"),new {engine=Common.FindEngine(Common.Base)});return 0;
            }
            if(args.Length==2&&args[0]=="--registration-plan"){
                Common.WriteJson(Path.GetFullPath(args[1]),new {hive="HKEY_CURRENT_USER",installRoot=Common.InstallRoot,extensions=Common.Extensions,command=Common.OpenCommand(Common.InstallRoot),writesUserChoice=false,setsDefault=false,version=Common.Version});return 0;
            }
            var form=new Form{Text="FullArcCAD セットアップ",ClientSize=new Size(640,330),StartPosition=FormStartPosition.CenterScreen,FormBorderStyle=FormBorderStyle.FixedDialog,MaximizeBox=false};
            var title=new Label{Text="FullArcCAD をインストール",Font=new Font(SystemFonts.MessageBoxFont.FontFamily,15,FontStyle.Bold),Left=24,Top=20,Width=580,Height=34};
            var info=new Label{Text="このユーザー専用にインストールします。FreeCAD本体は別途必要です。\nSTEPなどの「プログラムから開く」にFullArcCADを追加します。",Left=24,Top=65,Width=590,Height=46};
            var engine=new TextBox{Text=Common.FindEngine(Common.Base),Left=24,Top=139,Width=485};
            var engineLabel=new Label{Text="FreeCAD の実行ファイル",Left=24,Top=117,Width=500};
            var browse=new Button{Text="参照…",Left=518,Top=136,Width=95};browse.Click+=(s,e)=>{using(var dialog=new OpenFileDialog{Filter="FreeCAD (freecad.exe)|freecad.exe"})if(dialog.ShowDialog()==DialogResult.OK)engine.Text=dialog.FileName;};
            var path=new Label{Text="保存先: "+Common.InstallRoot,Left=24,Top=177,Width=590,Height=36};
            var desktop=new CheckBox{Text="デスクトップにショートカットを作成",Checked=true,Left=24,Top=221,Width=450};
            var install=new Button{Text="インストール",Left=398,Top=274,Width=110};var cancel=new Button{Text="キャンセル",Left=518,Top=274,Width=95};cancel.Click+=(s,e)=>form.Close();
            install.Click+=(s,e)=>{
                try {
                    string exe=Path.GetFullPath(engine.Text);
                    if(!File.Exists(exe)||!Path.GetFileName(exe).Equals("freecad.exe",StringComparison.OrdinalIgnoreCase))throw new IOException("FreeCADのfreecad.exeを指定してください。");
                    install.Enabled=false;cancel.Enabled=false;form.Cursor=Cursors.WaitCursor;
                    Install(Common.InstallRoot,exe,desktop.Checked);form.Cursor=Cursors.Default;
                    MessageBox.Show("インストールが完了しました。\nSTEPを右クリック → プログラムから開く → FullArcCAD を選べます。\n既定のアプリはWindowsの設定画面で選択してください。","FullArcCAD",MessageBoxButtons.OK,MessageBoxIcon.Information);form.Close();
                }catch(Exception error){form.Cursor=Cursors.Default;install.Enabled=true;cancel.Enabled=true;MessageBox.Show(error.Message,"FullArcCAD",MessageBoxButtons.OK,MessageBoxIcon.Error);}
            };
            form.Controls.AddRange(new Control[]{title,info,engineLabel,engine,browse,path,desktop,install,cancel});Application.Run(form);return 0;
        }catch(Exception error){MessageBox.Show(error.Message,"FullArcCAD Setup",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
    }
}
