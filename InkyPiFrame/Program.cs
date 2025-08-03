using System.Diagnostics;
using System.Text.Json;

namespace InkyPiFrame;

public class Program
{
    private static readonly HttpClient httpClient = new();
    private static string immichBaseUrl = "";
    private static string apiKey = "";
    private static string pythonScriptPath = "./display.py";
    private static int rotationIntervalMinutes = 10;
    private static string tempImagePath = "/tmp/current_frame.jpg";

    public static async Task Main(string[] args)
    {
        Console.WriteLine("Inky PFrame starting up...");

        LoadConfiguration();

        httpClient.DefaultRequestHeaders.Add("x-api-key", apiKey);

        Console.WriteLine($"Connecting to Immich at: {immichBaseUrl}");
        Console.WriteLine($"Image rotation interval: {rotationIntervalMinutes} minutes");

        while (true)
        {
            try
            {
                await DisplayRandomPhoto();
                Console.WriteLine($"Waiting {rotationIntervalMinutes} minutes for next image...");
                await Task.Delay(TimeSpan.FromMinutes(rotationIntervalMinutes));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error in main loop: {ex.Message}");
                Console.WriteLine("Retrying in 1 minute...");
                await Task.Delay(TimeSpan.FromMinutes(1));
            }
        }
    }

    private static void LoadConfiguration()
    {
        immichBaseUrl = "http://10.0.1.41:30041";
        apiKey = "Emwmkf7IzakSyEYJAM8FvZGhX27kNRQjydh0nagY";

        var intervalStr = "10";
        if (int.TryParse(intervalStr, out int interval))
        {
            rotationIntervalMinutes = interval;
        }

        pythonScriptPath = "./display.py";
    }

    private static async Task DisplayRandomPhoto()
    {
        try
        {
            Console.WriteLine("Fetching random photo from Immich...");

            // Get random assets from Immich
            var randomAssets = await GetRandomAssets(10); // Fetch more to increase chance of finding a photo

            if (randomAssets == null || !randomAssets.Any())
            {
                Console.WriteLine("No photos found in Immich");
                return;
            }

            // Filter out .MOV files and videos
            var photoAsset = randomAssets
                .FirstOrDefault(a =>
                    !a.OriginalFileName.EndsWith(".mov", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(a.Type, "VIDEO", StringComparison.OrdinalIgnoreCase));

            if (photoAsset == null)
            {
                Console.WriteLine("No suitable photo found (all were videos or .MOV files)");
                return;
            }

            Console.WriteLine($"Selected photo: {photoAsset.OriginalFileName} ({photoAsset.Id})");

            // Download the photo
            var imageData = await DownloadAsset(photoAsset.Id);

            if (imageData == null)
            {
                Console.WriteLine("Failed to download image");
                return;
            }

            // Save to temporary file
            await File.WriteAllBytesAsync(tempImagePath, imageData);
            Console.WriteLine($"Image saved to: {tempImagePath}");

            // Call Python script to display the image
            var success = await UpdateDisplay(tempImagePath);

            if (success)
            {
                Console.WriteLine("Display updated successfully!");
            }
            else
            {
                Console.WriteLine("Failed to update display");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error displaying photo: {ex.Message}");
        }
    }

    private static async Task<List<ImmichAsset>> GetRandomAssets(int count)
    {
        try
        {
            var response = await httpClient.GetAsync($"{immichBaseUrl}/api/assets/random?count={count}");
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadAsStringAsync();
            var assets = JsonSerializer.Deserialize<List<ImmichAsset>>(json, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            return assets ?? new List<ImmichAsset>();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error fetching random assets: {ex.Message}");
            return new List<ImmichAsset>();
        }
    }

    private static async Task<byte[]> DownloadAsset(string assetId)
    {
        try
        {
            var response = await httpClient.GetAsync($"{immichBaseUrl}/api/assets/{assetId}/original");
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadAsByteArrayAsync();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error downloading asset {assetId}: {ex.Message}");
            return null;
        }
    }

    private static async Task<bool> UpdateDisplay(string imagePath)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"{pythonScriptPath} \"{imagePath}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = startInfo };
            process.Start();

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();

            await process.WaitForExitAsync();

            if (!string.IsNullOrEmpty(output))
            {
                Console.WriteLine($"Python output: {output}");
            }

            if (!string.IsNullOrEmpty(error))
            {
                Console.WriteLine($"Python error: {error}");
            }

            return process.ExitCode == 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error running Python script: {ex.Message}");
            return false;
        }
    }
    public class ImmichAsset
    {
        public string Id { get; set; } = "";
        public string OriginalFileName { get; set; } = "";
        public string Type { get; set; } = "";
        public DateTime FileCreatedAt { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
