using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Diagnostics;
using System.Windows.Forms;
using System.Collections.Generic;
[assembly: AssemblyTitle("FullArcCAD Uninstaller")]
[assembly: AssemblyVersion("0.2.266.0")]
internal static class Uninstall {
    [STAThread]static int Main(string[] args) {
        Application.EnableVisualStyles();
        bool silent=args.Length==2 && args[0]=="--remove-silent";
        if(silent)args[0]="--remove";
        try {
            if(args.Length!=2||args[0]!="--remove"){
                if(MessageBox.Show("FullArcCADをアンインストールしますか？\nモデルとユーザー設定は削除しません。","FullArcCAD",MessageBoxButtons.YesNo,MessageBoxIcon.Question)!=DialogResult.Yes)return 0;
                if(Common.EngineAlive(Common.StateRoot))throw new IOException("FullArcCADを閉じてから実行してください。");
                string helper=Path.Combine(Path.GetTempPath(),"FullArcCAD-Uninstall-"+Guid.NewGuid().ToString("N")+".exe");File.Copy(Assembly.GetExecutingAssembly().Location,helper);
                Process.Start(new ProcessStartInfo(helper,"--remove "+Common.Quote(Common.Base)){UseShellExecute=false,WindowStyle=ProcessWindowStyle.Hidden});return 0;
            }
            string root=Path.GetFullPath(args[1]);var manifest=Common.ReadJson(Path.Combine(root,"install-manifest.json"));
            if(Convert.ToString(manifest["productId"])!=Common.ProductId)throw new IOException("FullArcCADのインストール先ではありません。");
            if(!string.Equals(root,Common.InstallRoot,StringComparison.OrdinalIgnoreCase))throw new IOException("Unexpected installation directory");
            Common.Unregister(root);int kept=0;
            foreach(var item in (System.Collections.IEnumerable)manifest["files"]){var entry=(Dictionary<string,object>)item;string path=Common.SafePath(root,Convert.ToString(entry["path"]));
                if(File.Exists(path)){if(Common.Hash(path)==Convert.ToString(entry["sha256"])){
                    File.Delete(path);
                    if(path.EndsWith(".py",StringComparison.OrdinalIgnoreCase)){
                        string cache=Path.Combine(Path.GetDirectoryName(path),"__pycache__");
                        if(Directory.Exists(cache))foreach(string pyc in Directory.GetFiles(cache,Path.GetFileNameWithoutExtension(path)+".*.pyc"))File.Delete(pyc);
                    }
                }else kept++;}
            }
            File.Delete(Path.Combine(root,"install-manifest.json"));
            foreach(string file in new[]{Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs),"FullArcCAD-Native","FullArcCAD-Native.lnk"),Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),"FullArcCAD-Native.lnk")}){
                if(File.Exists(file))File.Delete(file);
            }
            foreach(string dir in Directory.GetDirectories(root,"*",SearchOption.AllDirectories).OrderByDescending(x=>x.Length))if(!Directory.EnumerateFileSystemEntries(dir).Any())Directory.Delete(dir);
            if(!Directory.EnumerateFileSystemEntries(root).Any())Directory.Delete(root);
            if(!silent)MessageBox.Show("FullArcCADを削除しました。\nユーザー設定と変更済みファイルは保持しました。","FullArcCAD",MessageBoxButtons.OK,MessageBoxIcon.Information);return 0;
        }catch(Exception error){if(!silent)MessageBox.Show(error.Message,"FullArcCAD",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
    }
}
