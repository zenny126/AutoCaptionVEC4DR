-- ============================================================
-- AutoCaption VEC - Generate Captions (Local Whisper)
-- Run this script in DaVinci Resolve via: Workspace > Scripts
--
-- Requirements:
--  1. Python 3.9+ installed
--  2. Dependencies: pip install -r requirements.txt
--  3. transcribe_local.py in same folder as this script
-- ============================================================

resolve = Resolve()
local isWindows = FuPLATFORM_WINDOWS

-- ============================================================
-- CONFIGURATION
-- ============================================================
local SCRIPT_DIR = debug.getinfo(1, "S").source:match("@?(.*[\\/])")
local PYTHON_SCRIPT_PATH = SCRIPT_DIR .. "transcribe_local.py"
local PYTHON_EXE = "python" -- change to "python3" on macOS if needed

-- ============================================================
-- Message box (Windows: PowerShell MessageBox)
-- ============================================================
local function showMessage(title, message, askYesNo)
    if isWindows then
        local buttons = askYesNo and "YesNo" or "OK"
        local icon = askYesNo and "Question" or "Information"
        local tmpPs1 = os.getenv("TEMP") .. "\\autocaption_vec_msgbox.ps1"
        local tmpOut = os.getenv("TEMP") .. "\\autocaption_vec_msgbox_result.txt"

        local f = io.open(tmpPs1, "w")
        f:write("Add-Type -AssemblyName System.Windows.Forms\n")
        f:write("$title = @'\n" .. title .. "\n'@\n")
        f:write("$message = @'\n" .. message .. "\n'@\n")
        f:write("$r = [System.Windows.Forms.MessageBox]::Show($message, $title, " ..
                "[System.Windows.Forms.MessageBoxButtons]::" .. buttons .. ", " ..
                "[System.Windows.Forms.MessageBoxIcon]::" .. icon .. ")\n")
        f:write("Set-Content -Path '" .. tmpOut .. "' -Value $r\n")
        f:close()

        os.execute('powershell -NoProfile -ExecutionPolicy Bypass -File "' .. tmpPs1 .. '"')

        local result = ""
        local rf = io.open(tmpOut, "r")
        if rf then
            result = rf:read("*l") or ""
            rf:close()
            os.remove(tmpOut)
        end
        os.remove(tmpPs1)
        return result:gsub("%s+", "") == "Yes"
    else
        local safeTitle = title:gsub('"', '\\"')
        local safeMessage = message:gsub('"', '\\"'):gsub("\n", " ")
        local buttons = askYesNo and '{"No", "Yes"}' or '{"OK"}'
        local osaCmd = string.format(
            'osascript -e \'display dialog "%s" with title "%s" buttons %s default button "%s"\'',
            safeMessage, safeTitle, buttons, askYesNo and "Yes" or "OK"
        )
        local f = io.popen(osaCmd)
        local result = f and f:read("*a") or ""
        if f then f:close() end
        return result:find("Yes") ~= nil
    end
end

-- ============================================================
-- File picker (Windows: PowerShell OpenFileDialog)
-- ============================================================
local function pickFile()
    if isWindows then
        local tmpPs1 = os.getenv("TEMP") .. "\\autocaption_vec_pickfile.ps1"
        local tmpOut = os.getenv("TEMP") .. "\\autocaption_vec_pickfile_result.txt"

        local f = io.open(tmpPs1, "w")
        f:write("Add-Type -AssemblyName System.Windows.Forms\n")
        f:write("$dlg = New-Object System.Windows.Forms.OpenFileDialog\n")
        f:write([[$dlg.Filter = "Media Files|*.mp4;*.mov;*.mkv;*.wav;*.mp3;*.m4a;*.avi|All Files|*.*"]] .. "\n")
        f:write("$dlg.Title = 'Select audio/video file to create subtitles'\n")
        f:write("if ($dlg.ShowDialog() -eq 'OK') {\n")
        f:write("  Set-Content -Path '" .. tmpOut .. "' -Value $dlg.FileName\n")
        f:write("} else {\n")
        f:write("  Set-Content -Path '" .. tmpOut .. "' -Value ''\n")
        f:write("}\n")
        f:close()

        os.execute('powershell -NoProfile -ExecutionPolicy Bypass -File "' .. tmpPs1 .. '"')

        local result = ""
        local rf = io.open(tmpOut, "r")
        if rf then
            result = rf:read("*l") or ""
            rf:close()
            os.remove(tmpOut)
        end
        os.remove(tmpPs1)
        if result == "" then return nil end
        return result
    else
        local osaCmd = "osascript -e 'POSIX path of (choose file with prompt \"Select audio/video file\")'"
        local f = io.popen(osaCmd)
        local result = f and f:read("*l") or ""
        if f then f:close() end
        if result == "" then return nil end
        return result
    end
end

-- ============================================================
-- Dialog to select input audio/video language & settings
-- ============================================================
local function pickLanguage()
    if isWindows then
        local tmpPs1 = os.getenv("TEMP") .. "\\autocaption_vec_picklang.ps1"
        local tmpOut = os.getenv("TEMP") .. "\\autocaption_vec_picklang_result.txt"

        local f = io.open(tmpPs1, "w")
        f:write([[
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "AutoCaption VEC - Settings"
$form.Size = New-Object System.Drawing.Size(500,350)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.Topmost = $true

# Language Label
$langLabel = New-Object System.Windows.Forms.Label
$langLabel.Text = "Source Language:"
$langLabel.Location = New-Object System.Drawing.Point(20,20)
$langLabel.Size = New-Object System.Drawing.Size(150,20)
$form.Controls.Add($langLabel)

# Language Dropdown
$langDropdown = New-Object System.Windows.Forms.ComboBox
$langDropdown.Items.AddRange(@("Vietnamese", "English", "Chinese", "Auto-detect"))
$langDropdown.SelectedIndex = 3
$langDropdown.Location = New-Object System.Drawing.Point(180,20)
$langDropdown.Size = New-Object System.Drawing.Size(280,25)
$langDropdown.DropDownStyle = "DropDownList"
$form.Controls.Add($langDropdown)

# Model Label
$modelLabel = New-Object System.Windows.Forms.Label
$modelLabel.Text = "Model:"
$modelLabel.Location = New-Object System.Drawing.Point(20,60)
$modelLabel.Size = New-Object System.Drawing.Size(150,20)
$form.Controls.Add($modelLabel)

# Model Dropdown
$modelDropdown = New-Object System.Windows.Forms.ComboBox
$modelDropdown.Items.AddRange(@("tiny", "base", "small", "medium", "large-v3"))
$modelDropdown.SelectedIndex = 3
$modelDropdown.Location = New-Object System.Drawing.Point(180,60)
$modelDropdown.Size = New-Object System.Drawing.Size(280,25)
$modelDropdown.DropDownStyle = "DropDownList"
$form.Controls.Add($modelDropdown)

# Output Files Label
$outputLabel = New-Object System.Windows.Forms.Label
$outputLabel.Text = "Output Files:"
$outputLabel.Location = New-Object System.Drawing.Point(20,100)
$outputLabel.Size = New-Object System.Drawing.Size(150,20)
$form.Controls.Add($outputLabel)

# Output Files Dropdown
$outputDropdown = New-Object System.Windows.Forms.ComboBox
$outputDropdown.Items.AddRange(@("1 File (Original only)", "2 Files (Original + Translation)"))
$outputDropdown.SelectedIndex = 0
$outputDropdown.Location = New-Object System.Drawing.Point(180,100)
$outputDropdown.Size = New-Object System.Drawing.Size(280,25)
$outputDropdown.DropDownStyle = "DropDownList"
$form.Controls.Add($outputDropdown)

# Translation Language Label
$transLabel = New-Object System.Windows.Forms.Label
$transLabel.Text = "Translation Language:"
$transLabel.Location = New-Object System.Drawing.Point(20,140)
$transLabel.Size = New-Object System.Drawing.Size(150,20)
$transLabel.Enabled = $false
$form.Controls.Add($transLabel)

# Translation Language Dropdown
$transDropdown = New-Object System.Windows.Forms.ComboBox
$transDropdown.Items.AddRange(@("English", "Vietnamese", "Spanish", "French", "German", "Chinese", "Japanese", "Korean"))
$transDropdown.SelectedIndex = 0
$transDropdown.Location = New-Object System.Drawing.Point(180,140)
$transDropdown.Size = New-Object System.Drawing.Size(280,25)
$transDropdown.DropDownStyle = "DropDownList"
$transDropdown.Enabled = $false
$form.Controls.Add($transDropdown)

# Event: Enable/Disable translation language based on output format
$outputDropdown.Add_SelectedIndexChanged({
    if ($outputDropdown.SelectedIndex -eq 0) {
        $transLabel.Enabled = $false
        $transDropdown.Enabled = $false
    } else {
        $transLabel.Enabled = $true
        $transDropdown.Enabled = $true
    }
})

# OK Button
$okBtn = New-Object System.Windows.Forms.Button
$okBtn.Text = "OK"
$okBtn.Location = New-Object System.Drawing.Point(180,200)
$okBtn.Size = New-Object System.Drawing.Size(90,35)
$okBtn.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($okBtn)

# Cancel Button
$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = "Cancel"
$cancelBtn.Location = New-Object System.Drawing.Point(280,200)
$cancelBtn.Size = New-Object System.Drawing.Size(90,35)
$cancelBtn.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancelBtn)

$form.AcceptButton = $okBtn
$form.CancelButton = $cancelBtn

$result = $form.ShowDialog()

if ($result -eq "OK") {
    $lang = switch ($langDropdown.SelectedIndex) {
        0 { "vi" }
        1 { "en" }
        2 { "zh" }
        default { "auto" }
    }
    
    $model = $modelDropdown.SelectedItem
    
    $output = if ($outputDropdown.SelectedIndex -eq 0) { "1" } else { "2" }
    
    $trans = switch ($transDropdown.SelectedIndex) {
        0 { "en" }
        1 { "vi" }
        2 { "es" }
        3 { "fr" }
        4 { "de" }
        5 { "zh" }
        6 { "ja" }
        7 { "ko" }
        default { "en" }
    }
    
    Set-Content -Path "]] .. tmpOut .. [[" -Value "$lang|$model|$output|$trans"
} else {
    Set-Content -Path "]] .. tmpOut .. [[" -Value "CANCEL"
}
]])
        f:close()

        os.execute('powershell -NoProfile -ExecutionPolicy Bypass -File "' .. tmpPs1 .. '"')
        os.execute("timeout /t 1 /nobreak >nul 2>&1")

        local result = ""
        local rf = io.open(tmpOut, "r")
        if rf then
            result = rf:read("*l") or "CANCEL"
            rf:close()
            os.remove(tmpOut)
        end
        os.remove(tmpPs1)

        if result == "CANCEL" then
            return nil, nil, nil, nil
        end

        local parts = {}
        for part in result:gmatch("[^|]+") do
            table.insert(parts, part)
        end

        local lang = parts[1] == "auto" and nil or parts[1]
        local model = parts[2]
        local output = parts[3]
        local trans = parts[4]

        print("DEBUG: lang=" .. tostring(lang) .. ", model=" .. model .. ", output=" .. output .. ", trans=" .. trans)
        return lang, model, output, trans
    else
        -- Default values for macOS if UI is bypassed
        return nil, "medium", "1", "en"
    end
end

-- ============================================================
-- Call Python to transcribe
-- ============================================================
local function runTranscribe(inputPath, outputSrtPath, language, model, outputFiles, targetLang)
    local envPrefix = isWindows and "set PYTHONIOENCODING=utf-8 && " or "PYTHONIOENCODING=utf-8 "
    local cmd = string.format(
        '%s%s "%s" "%s" "%s" "%s" "%s" "%s" "%s"',
        envPrefix, PYTHON_EXE, PYTHON_SCRIPT_PATH, inputPath, outputSrtPath, language or "", model or "medium", targetLang or "", outputFiles or "1"
    )
    
    print("Running: " .. cmd)
    print("Processing with local Whisper (CPU) - may take a few minutes depending on file length and model. Please wait...")

    local handle = io.popen(cmd .. " 2>&1")
    local output = handle:read("*a")
    local ok, exitType, exitCode = handle:close()
    print("---- Python output ----")
    print(output)
    print("------------------------")

    local success = output:find("OK:") ~= nil
    return success, output
end

-- ============================================================
-- Import SRT files into current timeline
-- ============================================================
local function importSrtToTimeline(srtPath, translatedSrtPath)
    local projectManager = resolve:GetProjectManager()
    local project = projectManager:GetCurrentProject()
    if not project then
        return false, "Cannot find open project."
    end

    local timeline = project:GetCurrentTimeline()
    if not timeline then
        return false, "Cannot find open timeline. Please open a timeline first."
    end

    local mediaPool = project:GetMediaPool()

    -- Import original SRT file
    local importedItems = mediaPool:ImportMedia({ srtPath })
    if not importedItems or #importedItems == 0 then
        return false, "Failed to import SRT file to Media Pool."
    end

    local appended = mediaPool:AppendToTimeline(importedItems)
    if not appended or #appended == 0 then
        return false, "Imported to Media Pool but failed to add to timeline. You can manually drag the SRT file from Media Pool to timeline."
    end

    -- Import translated SRT file if it exists
    if translatedSrtPath and os.rename(translatedSrtPath, translatedSrtPath) then
        local translatedItems = mediaPool:ImportMedia({ translatedSrtPath })
        if translatedItems and #translatedItems > 0 then
            mediaPool:AppendToTimeline(translatedItems)
        end
    end

    return true, "Successfully added subtitle(s) to timeline."
end

-- ============================================================
-- MAIN
-- ============================================================
local function Main()
    print("=== AutoCaption VEC - Generate Captions ===")

    local inputFile = pickFile()
    if not inputFile then
        print("Cancelled by user.")
        return
    end
    print("Selected file: " .. inputFile)

    -- single form captures all parameters now
    local selectedLang, model, outputFormat, targetLang = pickLanguage()
    if not model then
        print("Cancelled by user.")
        return
    end

    local srtOutput = (os.getenv("TEMP") or "/tmp") .. "/autocaption_vec_output.srt"
    if not isWindows then
        srtOutput = "/tmp/autocaption_vec_output.srt"
    end

    local success, log = runTranscribe(inputFile, srtOutput, selectedLang, model, outputFormat, targetLang)
    if not success then
        showMessage("AutoCaption VEC", "Failed to create subtitles.\n\nDetails logged in Console.", false)
        return
    end

    -- Determine translated file path
    local translatedSrtOutput = nil
    if outputFormat == "2" and targetLang then
        local baseDir = string.match(srtOutput, "^(.*)[/\\]")
        translatedSrtOutput = baseDir .. "/autocaption_vec_output_" .. targetLang .. ".srt"
    end

    local importOk, importMsg = importSrtToTimeline(srtOutput, translatedSrtOutput)
    if importOk then
        local msgText = outputFormat == "2" and "Successfully created and added subtitle files to timeline!" or "Successfully created and added subtitle to timeline!"
        showMessage("AutoCaption VEC", msgText, false)
    else
        showMessage("AutoCaption VEC",
            "Created subtitle file(s) at:\n" .. srtOutput ..
            (translatedSrtOutput and "\n" .. translatedSrtOutput or "") ..
            "\n\nBut failed to add to timeline: " .. importMsg, false)
    end
end

local ok, err = pcall(Main)
if not ok then
    print("Error: " .. tostring(err))
end