using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using Microsoft.Win32;

internal static class Common {
    internal const string ProductId="d05ea4b8-43eb-4de2-85f0-29a417668302";
    internal const string Version="0.2.266-alpha.windows1";
    internal const string ProgId="FullArcCAD.Native.Document";
    internal static readonly string[] Extensions={".step",".stp",".fcstd",".stl",".glb",".gltf",".iges",".igs",".brep",".obj",".ply",".off"};
    internal static readonly JavaScriptSerializer Json=new JavaScriptSerializer { MaxJsonLength=32*1024*1024 };
#if SELF_TEST
    internal static string TestRegistryRoot;
#endif
    internal static string RegPath(string path){
#if SELF_TEST
        if(string.IsNullOrEmpty(TestRegistryRoot)||!TestRegistryRoot.StartsWith(@"Software\FullArcCAD-Native.InstallerTests.",StringComparison.Ordinal))throw new InvalidOperationException("Invalid isolated registry test root");
        return TestRegistryRoot+"\\"+path;
#else
        return path;
#endif
    }
    internal static void Notify(){
#if !SELF_TEST
        SHChangeNotify(0x08000000,0,IntPtr.Zero,IntPtr.Zero);
#endif
    }
    internal static string Base {get{return AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);}}
    internal static string Local {get{return Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);}}
    internal static string InstallRoot {get{return Path.Combine(Local,"Programs","FullArcCAD-Native");}}
    internal static string StateRoot {get{return Environment.GetEnvironmentVariable("FULLARCCAD_STATE_DIR")??Path.Combine(Local,"FullArcCAD-Native");}}
    internal static string Quote(string s) {
        var b=new StringBuilder("\"");int n=0;
        foreach(char c in s){if(c=='\\'){n++;continue;}if(c=='\"'){b.Append('\\',n*2+1);b.Append(c);}else{b.Append('\\',n);b.Append(c);}n=0;}
        b.Append('\\',n*2);b.Append('"');return b.ToString();
    }
    internal static string Hash(string p){using(var s=File.OpenRead(p))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(s)).Replace("-","").ToLowerInvariant();}
    internal static string SafePath(string root,string relative) {
        if(Path.IsPathRooted(relative))throw new IOException("Absolute package path rejected");
        string r=Path.GetFullPath(root).TrimEnd('\\')+"\\";string p=Path.GetFullPath(Path.Combine(root,relative));
        if(!p.StartsWith(r,StringComparison.OrdinalIgnoreCase))throw new IOException("Package path outside install folder");return p;
    }
    internal static void WriteJson(string p,object o){Directory.CreateDirectory(Path.GetDirectoryName(p));File.WriteAllText(p,Json.Serialize(o),new UTF8Encoding(false));}
    internal static Dictionary<string,object> ReadJson(string p){return Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(p,Encoding.UTF8));}
    internal static string FindEngine(string root) {
        string selected=Environment.GetEnvironmentVariable("FULLARCCAD_ENGINE");
        if(!string.IsNullOrWhiteSpace(selected)){
            string chosen=Path.GetFullPath(selected);
            if(!File.Exists(chosen))throw new IOException("FULLARCCAD_ENGINE does not point to an existing FreeCAD.exe.");
            return chosen;
        }
        string config=Path.Combine(root,"launcher.json");
        if(File.Exists(config)){var j=ReadJson(config);object v;if(j.TryGetValue("engine",out v)&&File.Exists(Convert.ToString(v)))return Path.GetFullPath(Convert.ToString(v));}
        foreach(string parent in new[]{Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86)}){
            if(!Directory.Exists(parent))continue;
            foreach(string d in Directory.GetDirectories(parent,"FreeCAD*").OrderByDescending(x=>x)){
                string exe=Path.Combine(d,"bin","freecad.exe");if(File.Exists(exe))return exe;
            }
        }
        return "";
    }
    internal static void ValidateEngine(string engine) {
        if(!File.Exists(engine)||!Path.GetFileName(engine).Equals("freecad.exe",StringComparison.OrdinalIgnoreCase))throw new IOException("FreeCAD.exeを指定してください。");
        string python=Path.Combine(Path.GetDirectoryName(engine),"python311.dll");
        if(!File.Exists(python))throw new IOException("Python 3.11 64bitを内蔵したFreeCADが必要です。");
        using(var stream=File.OpenRead(python))using(var reader=new BinaryReader(stream)){
            stream.Position=0x3c;int offset=reader.ReadInt32();stream.Position=offset;
            if(reader.ReadUInt32()!=0x4550 || reader.ReadUInt16()!=0x8664)throw new IOException("64bit版FreeCADが必要です。");
        }
    }
    internal static bool EngineAlive(string state) {
        try {var j=ReadJson(Path.Combine(state,"session.json"));var p=Process.GetProcessById(Convert.ToInt32(j["pid"]));return !p.HasExited&&p.StartTime.ToUniversalTime().Ticks==Convert.ToInt64(j["startTicks"]);}
        catch{return false;}
    }
    internal static string OpenCommand(string root){return Quote(Path.Combine(root,"FullArcCAD.exe"))+" "+Quote("%1");}
    internal static void Value(string key,string name,object value){using(var k=Registry.CurrentUser.CreateSubKey(RegPath(key)))k.SetValue(name,value);}
    internal static void Register(string root) {
        string exe=Path.Combine(root,"FullArcCAD.exe"),cmd=OpenCommand(root);
        string own=@"Software\Classes\"+ProgId;
        Value(own,"","FullArcCAD CAD document");Value(own,"FriendlyTypeName","FullArcCAD CAD document");Value(own+@"\DefaultIcon","",Quote(exe)+",0");Value(own+@"\shell\open\command","",cmd);
        string app=@"Software\Classes\Applications\FullArcCAD-Native.exe";
        Value(app,"FriendlyAppName","FullArcCAD Native");Value(app+@"\shell\open\command","",cmd);
        foreach(string ext in Extensions){Value(app+@"\SupportedTypes",ext,"");Value(@"Software\Classes\"+ext+@"\OpenWithProgids",ProgId,"");Value(@"Software\FullArcCAD-Native\Capabilities\FileAssociations",ext,ProgId);}
        Value(@"Software\FullArcCAD-Native\Capabilities","ApplicationName","FullArcCAD Native");Value(@"Software\FullArcCAD-Native\Capabilities","ApplicationDescription","FullArcCAD CAD / mesh application powered by installed FreeCAD");Value(@"Software\FullArcCAD-Native\Capabilities","ApplicationIcon",Quote(exe)+",0");
        Value(@"Software\RegisteredApplications","FullArcCAD-Native",@"Software\FullArcCAD-Native\Capabilities");Value(@"Software\FullArcCAD-Native","InstallPath",root);
        string u=@"Software\Microsoft\Windows\CurrentVersion\Uninstall\FullArcCAD-Native";
        Value(u,"DisplayName","FullArcCAD Native Preview");Value(u,"DisplayVersion",Version);Value(u,"Publisher","FullArcCAD local build");Value(u,"InstallLocation",root);Value(u,"DisplayIcon",exe);Value(u,"UninstallString",Quote(Path.Combine(root,"FullArcCAD-Uninstall.exe")));Value(u,"NoModify",1);Value(u,"NoRepair",1);
        Notify();
    }
    internal static void Shortcut(string file,string exe) {
        Directory.CreateDirectory(Path.GetDirectoryName(file));object shell=null,link=null;
        try {var type=Type.GetTypeFromProgID("WScript.Shell");shell=Activator.CreateInstance(type);link=type.InvokeMember("CreateShortcut",BindingFlags.InvokeMethod,null,shell,new object[]{file});
            var t=link.GetType();t.InvokeMember("TargetPath",BindingFlags.SetProperty,null,link,new object[]{exe});t.InvokeMember("WorkingDirectory",BindingFlags.SetProperty,null,link,new object[]{Path.GetDirectoryName(exe)});t.InvokeMember("IconLocation",BindingFlags.SetProperty,null,link,new object[]{exe+",0"});t.InvokeMember("Save",BindingFlags.InvokeMethod,null,link,null);
        } finally {if(link!=null)Marshal.FinalReleaseComObject(link);if(shell!=null)Marshal.FinalReleaseComObject(shell);}
    }
    internal static void Unregister(string root) {
        using(var k=Registry.CurrentUser.OpenSubKey(RegPath(@"Software\FullArcCAD-Native")))if(k==null||!string.Equals(Convert.ToString(k.GetValue("InstallPath")),root,StringComparison.OrdinalIgnoreCase))return;
        foreach(string ext in Extensions)using(var k=Registry.CurrentUser.OpenSubKey(RegPath(@"Software\Classes\"+ext+@"\OpenWithProgids"),true))if(k!=null)k.DeleteValue(ProgId,false);
        foreach(string path in new[]{@"Software\Classes\"+ProgId,@"Software\Classes\Applications\FullArcCAD-Native.exe",@"Software\FullArcCAD-Native",@"Software\Microsoft\Windows\CurrentVersion\Uninstall\FullArcCAD-Native"})Registry.CurrentUser.DeleteSubKeyTree(RegPath(path),false);
        using(var k=Registry.CurrentUser.OpenSubKey(RegPath(@"Software\RegisteredApplications"),true))if(k!=null)k.DeleteValue("FullArcCAD-Native",false);
        Notify();
    }
    [DllImport("shell32.dll")]static extern void SHChangeNotify(uint e,uint flags,IntPtr a,IntPtr b);
}
