# PROJECT FURNACE - STREFA 6: GÓRA (Centrum Dowodzenia)
# File: build_hud.ps1
# Description: PowerShell script to automatically scaffold, write code, and build
# the .NET 8 C# FurnaceHUD.exe Tactical Dashboard for Windows 11.

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " PROJECT FURNACE - AUTOMATED HUD BUILD SYSTEM (.NET 8 C#)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkDir = "$PSScriptRoot\FurnaceHUD"
if (-not (Test-Path $WorkDir)) {
    New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
    Write-Host "[+] Created project directory: $WorkDir" -ForegroundColor Green
}

# 1. Generate FurnaceHUD.csproj
$CsprojContent = @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>false</SelfContained>
  </PropertyGroup>
</Project>
"@

Set-Content -Path "$WorkDir\FurnaceHUD.csproj" -Value $CsprojContent -Encoding UTF8
Write-Host "[+] Created FurnaceHUD.csproj" -ForegroundColor Green

# 2. Generate Program.cs
$ProgramCsContent = @"
using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace FurnaceHUD
{
    class Program
    {
        private static string s_lastGps = "NO_FIX (0.0000, 0.0000)";
        private static string s_lastSigint = "NO_SIGNAL";
        private static int s_pixelTargets = 0;
        private static string s_lastPixelTime = "N/A";
        private static long s_packetCountPixel = 0;
        private static long s_packetCountPS4 = 0;

        static async Task Main(string[] args)
        {
            Console.Title = "PROJECT FURNACE - TACTICAL C4ISR HUD";
            Console.CursorVisible = false;
            Console.Clear();

            string ps4Host = Environment.GetEnvironmentVariable("PS4_HOST") ?? "CAMERA_HOST";
            int ps4Port = int.TryParse(Environment.GetEnvironmentVariable("PS4_PORT"), out int p1) ? p1 : 9090;
            int pixelListenPort = int.TryParse(Environment.GetEnvironmentVariable("PIXEL_LISTEN_PORT"), out int p2) ? p2 : 9091;

            CancellationTokenSource cts = new CancellationTokenSource();

            // Task 1: Render Loop
            Task renderTask = Task.Run(() => RenderHUDLoop(cts.Token));

            // Task 2: Listen for Pixel TCP Telemetry
            Task pixelTask = Task.Run(() => ListenPixelTCP(pixelListenPort, cts.Token));

            // Task 3: Connect to PS4 Blackbox TCP Server
            Task ps4Task = Task.Run(() => ConnectPS4Blackbox(ps4Host, ps4Port, cts.Token));

            Console.CancelKeyPress += (s, e) =>
            {
                e.Cancel = true;
                cts.Cancel();
            };

            await Task.WhenAll(renderTask, pixelTask, ps4Task);
        }

        private static async Task ListenPixelTCP(int port, CancellationToken token)
        {
            TcpListener listener = new TcpListener(IPAddress.Any, port);
            try
            {
                listener.Start();
                while (!token.IsCancellationRequested)
                {
                    TcpClient client = await listener.AcceptTcpClientAsync(token);
                    _ = Task.Run(() => HandlePixelClient(client, token), token);
                }
            }
            catch (Exception) { }
            finally { listener.Stop(); }
        }

        private static async Task HandlePixelClient(TcpClient client, CancellationToken token)
        {
            using (client)
            using (NetworkStream stream = client.GetStream())
            using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
            {
                while (!token.IsCancellationRequested && client.Connected)
                {
                    string? line = await reader.ReadLineAsync(token);
                    if (string.IsNullOrEmpty(line)) break;

                    try
                    {
                        using (JsonDocument doc = JsonDocument.Parse(line))
                        {
                            JsonElement root = doc.RootElement;
                            if (root.TryGetProperty("target_count", out JsonElement tc))
                            {
                                s_pixelTargets = tc.GetInt32();
                            }
                            if (root.TryGetProperty("timestamp", out JsonElement ts))
                            {
                                s_lastPixelTime = ts.GetString() ?? "N/A";
                            }
                            Interlocked.Increment(ref s_packetCountPixel);
                        }
                    }
                    catch { }
                }
            }
        }

        private static async Task ConnectPS4Blackbox(string host, int port, CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    using (TcpClient client = new TcpClient())
                    {
                        await client.ConnectAsync(host, port, token);
                        using (NetworkStream stream = client.GetStream())
                        using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
                        {
                            while (!token.IsCancellationRequested && client.Connected)
                            {
                                string? line = await reader.ReadLineAsync(token);
                                if (string.IsNullOrEmpty(line)) break;

                                try
                                {
                                    using (JsonDocument doc = JsonDocument.Parse(line))
                                    {
                                        JsonElement root = doc.RootElement;
                                        if (root.TryGetProperty("type", out JsonElement typeElem))
                                        {
                                            string type = typeElem.GetString() ?? "";
                                            if (type == "GPS_UPDATE" && root.TryGetProperty("data", out JsonElement gpsData))
                                            {
                                                double lat = gpsData.GetProperty("latitude").GetDouble();
                                                double lon = gpsData.GetProperty("longitude").GetDouble();
                                                string status = gpsData.GetProperty("status").GetString() ?? "UNKNOWN";
                                                s_lastGps = $"{status} ({lat:F6}, {lon:F6})";
                                            }
                                            else if ((type == "SIGINT_DATA" || type == "SIGINT_ALERT") && root.TryGetProperty("data", out JsonElement sigData))
                                            {
                                                double freq = sigData.GetProperty("frequency_mhz").GetDouble();
                                                double dbm = sigData.GetProperty("signal_dbm").GetDouble();
                                                string portName = sigData.GetProperty("port").GetString() ?? "UART";
                                                s_lastSigint = $"[{portName}] {freq:F2} MHz @ {dbm:F1} dBm";
                                            }
                                        }
                                        Interlocked.Increment(ref s_packetCountPS4);
                                    }
                                }
                                catch { }
                            }
                        }
                    }
                }
                catch
                {
                    await Task.Delay(2000, token);
                }
            }
        }

        private static void RenderHUDLoop(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                Console.SetCursorPosition(0, 0);
                string now = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss.fff");

                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("==================================================================================");
                Console.WriteLine("                      PROJECT FURNACE - C4ISR TACTICAL HUD                        ");
                Console.WriteLine("==================================================================================");
                Console.ResetColor();

                Console.ForegroundColor = ConsoleColor.DarkGray;
                Console.WriteLine($" SYSTEM TIME (UTC) : {now} | STATUS: OPERATIONAL");
                Console.WriteLine("----------------------------------------------------------------------------------");
                Console.ResetColor();

                // STREFA 1 - PIXEL TEREN
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine(" [STREFA 1] TEREN (Pixel Node / PTZ Vision):");
                Console.ResetColor();
                Console.WriteLine($"   - Last Frame UTC   : {s_lastPixelTime}");
                Console.ForegroundColor = s_pixelTargets > 0 ? ConsoleColor.Red : ConsoleColor.Green;
                Console.WriteLine($"   - Detected Targets : {s_pixelTargets} {(s_pixelTargets > 0 ? "!!! ALERT !!!" : "[CLEAR]")}");
                Console.ResetColor();
                Console.WriteLine($"   - Packets Received : {Interlocked.Read(ref s_packetCountPixel)}");
                Console.WriteLine("----------------------------------------------------------------------------------");

                // STREFA 3 & 4 - BLACKBOX / SIGINT
                Console.ForegroundColor = ConsoleColor.Magenta;
                Console.WriteLine(" [STREFA 3 & 4] KOCIOŁ / BLACKBOX (PS4 Linux SIGINT & GPS):");
                Console.ResetColor();
                Console.WriteLine($"   - GPS / NTP Fix    : {s_lastGps}");
                Console.ForegroundColor = s_lastSigint.Contains("ALERT") ? ConsoleColor.Red : ConsoleColor.Cyan;
                Console.WriteLine($"   - SIGINT Telemetry : {s_lastSigint}");
                Console.ResetColor();
                Console.WriteLine($"   - Packets Received : {Interlocked.Read(ref s_packetCountPS4)}");
                Console.WriteLine("----------------------------------------------------------------------------------");

                Console.ForegroundColor = ConsoleColor.DarkGray;
                Console.WriteLine(" Press CTRL+C to terminate HUD Node.");
                Console.ResetColor();

                Thread.Sleep(200);
            }
        }
    }
}
"@

Set-Content -Path "$WorkDir\Program.cs" -Value $ProgramCsContent -Encoding UTF8
Write-Host "[+] Created Program.cs" -ForegroundColor Green

# 3. Compile Project using dotnet CLI
Write-Host "[*] Compiling FurnaceHUD.exe via dotnet SDK..." -ForegroundColor Yellow

Push-Location $WorkDir
try {
    dotnet build -c Release
    Write-Host "[SUCCESS] FurnaceHUD.exe compiled successfully!" -ForegroundColor Green
    Write-Host "Binary Location: $WorkDir\bin\Release\net8.0\FurnaceHUD.exe" -ForegroundColor Green
}
catch {
    Write-Host "[WARNING] 'dotnet' build failed or SDK not found. Project files scaffolded in $WorkDir." -ForegroundColor Red
}
finally {
    Pop-Location
}
