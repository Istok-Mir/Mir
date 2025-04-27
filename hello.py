from Mir.package_storage import PackageStorage

# TODO: remove this...
p = PackageStorage('Mir')
# p.copy('./popup.css')
# p.copy('./api')
# p.rm('./popup.css')
# p.rm('./api')
print('same', p.is_same("./popup.css"))
