#******************************************************************************
#
#  @(#)__init__.py	3.4  01/09/24 CSS
#
#  "splot" Release 3
#
#  Copyright (c) 2016,2020,2023,2024
#  by Certified Scientific Software.
#  All rights reserved.
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software ("splot") and associated documentation files (the
#  "Software"), to deal in the Software without restriction, including
#  without limitation the rights to use, copy, modify, merge, publish,
#  distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so, subject to
#  the following conditions:
#
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
#
#  Neither the name of the copyright holder nor the names of its contributors
#  may be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
#     * The software is provided "as is", without warranty of any   *
#     * kind, express or implied, including but not limited to the  *
#     * warranties of merchantability, fitness for a particular     *
#     * purpose and noninfringement.  In no event shall the authors *
#     * or copyright holders be liable for any claim, damages or    *
#     * other liability, whether in an action of contract, tort     *
#     * or otherwise, arising from, out of or in connection with    *
#     * the software or the use of other dealings in the software.  *
#
#******************************************************************************

import os
import glob
try:
   import importlib.util
   using_imp = False
except ImportError:
   import imp
   using_imp = True

from SPlotTheme import SPlotTheme

#
# Prepare the path to look for themes
#
themes_path_var = os.environ.get("SPLOT_THEMES",None)
if themes_path_var is None:
   themes_all_path = []
else:
   themes_all_path = themes_path_var.split(":")

_themes_path = os.path.dirname(os.path.abspath(__file__))
themes_all_path.append( _themes_path )

all_themes = {}

for theme_dir in themes_all_path:

    for theme_file in glob.glob(os.path.join(theme_dir,"*.py")):

        if os.path.basename(theme_file) == "__init__.py":
              continue

        theme_name = os.path.splitext(os.path.basename(theme_file))[0]

        try:
            if using_imp:
                mod = imp.load_module(theme_name, open(theme_file), theme_file, ("py","U",1))
            else:
                sp = importlib.util.spec_from_file_location(theme_name, theme_file)
                mod = importlib.util.module_from_spec(sp)
                sp.loader.exec_module(mod)
            if hasattr(mod,'themes'):
                for name in mod.themes.keys():
                     theme_class = mod.themes[name]
                     if issubclass(theme_class, SPlotTheme):
                         all_themes[name] = mod.themes[name]
                     else:
                         dprint("Theme with name %s does not seem to be a Theme class",name)
        except:
            import traceback
            traceback.print_exc()

def get_themes():
    return list(all_themes.keys())

def get_theme(theme_name):
    if theme_name not in all_themes:
        theme_name = "spec"  
    if theme_name in all_themes:
        return all_themes[theme_name]()
    else:
        return None
