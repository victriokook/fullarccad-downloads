using System;
using System.IO;
using System.Linq;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;
using System.Security.Principal;
using System.Security.Cryptography;
using System.Text;
using System.Reflection;
[assembly: AssemblyTitle("FullArcCAD")]
[assembly: AssemblyProduct("FullArcCAD")]
[assembly: AssemblyVersion("0.2.266.0")]
internal static class Launcher {
    [STAThread]static int Main(string[] args) {
        Application.EnableVisualStyles();
        try {
            if(args.Length==1&&args[0]=="--default-apps"){Process.Start(new ProcessStartInfo("ms-settings:defaultapps"){UseShellExecute=true});return 0;}
            string output=null;
            if(args.Length>=2&&args[0]=="--diagnose"){output=Path.GetFullPath(args[1]);args=args.Skip(2).ToArray();}
            string root=Common.Base,engine=Common.FindEngine(root),state=Path.GetFullPath(Common.StateRoot);
            string macro=Path.Combine(root,"runtime","Launch.FCMacro");
            string[] files=args.Select(x=>Path.GetFullPath(x)).ToArray();
            foreach(string f in files)if(!File.Exists(f)||!Common.Extensions.Contains(Path.GetExtension(f).ToLowerInvariant()))throw new IOException("対応するCADファイルがありません: "+f);
            if(!File.Exists(engine))throw new IOException("FreeCADが見つかりません。セットアップでFreeCADの場所を指定してください。");
            if(!File.Exists(macro))throw new IOException("FullArcCADの実行ファイルが不足しています。再インストールしてください。");
            Common.ValidateEngine(engine);
            string profile=Path.Combine(state,"profile","user.cfg");
            string command="--user-cfg "+Common.Quote(profile)+" "+Common.Quote(macro);
            if(output!=null){Common.WriteJson(output,new {engine=engine,macro=macro,arguments=command,files=files,state=state,openCommand=Common.OpenCommand(root)});return 0;}
            Directory.CreateDirectory(Path.Combine(state,"requests"));Directory.CreateDirectory(Path.Combine(state,"responses"));Directory.CreateDirectory(Path.GetDirectoryName(profile));
            string key;using(var sha=SHA256.Create())key=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(state.ToLowerInvariant()))).Replace("-","").Substring(0,16);
            using(var mutex=new Mutex(false,@"Local\FullArcCAD-"+WindowsIdentity.GetCurrent().User.Value+"-"+key)){
                bool held=false;
                try {
                    try{held=mutex.WaitOne(15000);}catch(AbandonedMutexException){held=true;}
                    if(!held)throw new IOException("FullArcCADの起動処理が混み合っています。少し待って再度開いてください。");
                    string id=Guid.NewGuid().ToString("N"),request=Path.Combine(state,"requests",id+".json");
                    string temp=request+".tmp";Common.WriteJson(temp,new {files=files});File.Move(temp,request);
                    if(!Common.EngineAlive(state)){
                        foreach(string p in new[]{"ready.json","startup_error.json"}){string f=Path.Combine(state,p);if(File.Exists(f))File.Delete(f);}
                        var start=new ProcessStartInfo(engine,command){UseShellExecute=false,WorkingDirectory=root,WindowStyle=ProcessWindowStyle.Hidden};
                        start.EnvironmentVariables["FULLARCCAD_STATE_DIR"]=state;
                        string data=Path.Combine(state,"freecad-data"),tempDir=Path.Combine(state,"temp");
                        Directory.CreateDirectory(data);Directory.CreateDirectory(tempDir);
                        start.EnvironmentVariables["FREECAD_USER_HOME"]=state;
                        start.EnvironmentVariables["FREECAD_USER_DATA"]=data;
                        start.EnvironmentVariables["FREECAD_USER_TEMP"]=tempDir;
                        var process=Process.Start(start);
                        Common.WriteJson(Path.Combine(state,"session.json"),new {pid=process.Id,startTicks=process.StartTime.ToUniversalTime().Ticks,root=root});
                        var deadline=DateTime.UtcNow.AddSeconds(120);
                        while(DateTime.UtcNow<deadline){
                            string failure=Path.Combine(state,"startup_error.json");
                            if(File.Exists(failure))throw new IOException(File.ReadAllText(failure));
                            if(File.Exists(Path.Combine(state,"ready.json")))break;
                            if(process.HasExited)throw new IOException("FreeCAD exited before FullArcCAD was ready.");
                            Thread.Sleep(250);
                        }
                        if(!File.Exists(Path.Combine(state,"ready.json")))throw new IOException("FullArcCAD startup timed out.");
                    }
                }finally{if(held)mutex.ReleaseMutex();}
            }
            return 0;
        }catch(Exception error){MessageBox.Show(error.Message,"FullArcCAD",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
    }
}
