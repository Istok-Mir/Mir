import sublime

css = sublime.load_resource("Packages/Mir/popup.css")

def hover_template(content: str):
    global css
    return f"""
    <html class="mir_popup">
        <style>{css}</style>
        <body>
        <div class="mir_popup_content">
            {content}
        </div>
        </body>
    </html>"""

