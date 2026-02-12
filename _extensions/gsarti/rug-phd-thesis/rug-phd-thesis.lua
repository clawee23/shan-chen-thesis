-- Check if the current output format is PDF
local is_pdf = (quarto and quarto.doc.is_format("pdf"))

function Span (el)
  -- Paragraph inline block for LaTeX
  if is_pdf and el.classes[1] == "paragraph" then
    local content_text = pandoc.utils.stringify(el.content)
    return pandoc.RawInline('latex', '\\paragraph*{' .. content_text .. '}')
  elseif is_pdf and el.classes[1] == "subparagraph" then
    local content_text = pandoc.utils.stringify(el.content)
    return pandoc.RawInline('latex', '\\subparagraph*{' .. content_text .. '}')
  end
  return el
end

-- Simplified function using string.gsub with pattern matching
local function process_quarto_base64(content)
    -- Use gsub to find and replace all instances in one pass
    local result = content:gsub("(\\QuartoMarkdownBase64%s*{)([^{}]*)(})", function(prefix, inner_content, suffix)
        -- Check if content looks like it's already base64 encoded
        local looks_like_base64 = not inner_content:match("[%s%[@%]%(%)%*_`#]")
        
        if not looks_like_base64 and inner_content ~= "" then
            local encoded_content = quarto.base64.encode(inner_content)
            io.stderr:write(string.format("Quarto Base64 Filter: Encoded '%s' -> '%s'\n", 
                inner_content, encoded_content))
            return prefix .. encoded_content .. suffix
        else
            -- Return unchanged if already encoded or empty
            return prefix .. inner_content .. suffix
        end
    end)
    
    return result
end

-- Filter function for RawBlock elements  
function RawBlock(el)
    if is_pdf and (el.format == "latex" or el.format == "tex") then
        local original_text = el.text
        local processed_text = process_quarto_base64(original_text)
        
        if processed_text ~= original_text then
            return pandoc.RawBlock(el.format, processed_text)
        end
    end
    return el
end

-- Lua filter to replace \texttt{} with custom formatting

-- Function to escape special LaTeX characters
function escape_latex(text)
  -- Escape special characters that need to be escaped in LaTeX
  local replacements = {
    ["\\"] = "\\textbackslash{}",  -- Must be first
    ["_"] = "\\_",
    ["%"] = "\\%",
    ["$"] = "\\$",
    ["&"] = "\\&",
    ["#"] = "\\#",
    ["{"] = "\\{",
    ["}"] = "\\}",
    ["^"] = "\\^{}",
    ["~"] = "\\~{}",
  }
  
  -- Apply replacements
  local escaped = text
  -- Handle backslash first
  escaped = escaped:gsub("\\", replacements["\\"])
  -- Then handle other characters
  for char, replacement in pairs(replacements) do
    if char ~= "\\" then
      escaped = escaped:gsub("%" .. char, replacement)
    end
  end
  
  return escaped
end

function RawInline(el)
  if el.format == "latex" or el.format == "tex" then
    -- Skip if it already contains our replacement to avoid recursion
    if el.text:match("\\fcolorbox{codeframe}") then
      return nil
    end
    
    -- Pattern to match \texttt{...}
    local modified = false
    local result = el.text:gsub("\\texttt(%s*){([^{}]*)}", function(space, content)
      modified = true
      -- Escape special characters in the content
      local escaped_content = escape_latex(content)
      -- Return with escaped content
      return "\\fcolorbox{codeframe}{codebg}{\\small\\texttt{" .. escaped_content .. "}}"
    end)
    
    -- Return modified element only if changes were made
    if modified then
      return pandoc.RawInline(el.format, result)
    end
  end
end

function RawBlock(el)
  if el.format == "latex" or el.format == "tex" then
    -- Skip if it already contains our replacement to avoid recursion
    if el.text:match("\\fcolorbox{codeframe}") then
      return nil
    end
    
    -- Pattern to match \texttt{...}
    local modified = false
    local result = el.text:gsub("\\texttt(%s*){([^{}]*)}", function(space, content)
      modified = true
      -- Escape special characters in the content
      local escaped_content = escape_latex(content)
      -- Return with escaped content
      return "\\fcolorbox{codeframe}{codebg}{\\small\\texttt{" .. escaped_content .. "}}"
    end)
    
    -- Return modified element only if changes were made
    if modified then
      return pandoc.RawBlock(el.format, result)
    end
  end
end

-- Handle inline code that might be converted to \texttt
function Code(el)
  -- Only process if output format is LaTeX
  if FORMAT:match("latex") then
    -- Escape special characters in the code
    local escaped_text = escape_latex(el.text)
    -- Create the custom LaTeX command with escaped text
    local latex_code = "\\fcolorbox{codeframe}{codebg}{\\small\\texttt{" .. escaped_text .. "}}"
    return pandoc.RawInline("latex", latex_code)
  end
end