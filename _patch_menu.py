import sys
import os

filepath = r"C:\Users\samde\Desktop\cv sam new ma3 kimi\web\templates\index_v3.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """function toggleMenu(){
 document.getElementById('navLinks').classList.toggle('open');
}"""

new = """function toggleMenu(){
 document.getElementById('navLinks').classList.toggle('open');
 document.getElementById('hamburger').classList.toggle('open');
 document.body.style.overflow = document.getElementById('navLinks').classList.contains('open') ? 'hidden' : '';
}
// Close menu on nav link click (mobile)
document.querySelectorAll('.nav-links a').forEach(function(link){
 link.addEventListener('click',function(){
  if(document.getElementById('navLinks').classList.contains('open')) toggleMenu();
 });
});"""

if old in content:
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS")
else:
    print("OLD TEXT NOT FOUND")
    # Debug: show surrounding characters
    idx = content.find('toggleMenu')
    if idx >= 0:
        print("Found at index", idx)
        snippet = content[idx:idx+200]
        print(repr(snippet))
