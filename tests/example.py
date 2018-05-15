#!/usr/bin/env python3
# Simple demonstration of using urlup programmatically.
# This requires urlup to be installed on your system.

from urlup import updated_urls

for result in updated_urls(['http://caltech.edu', 'http://notarealurl.nowhere']):
     print('Original URL: ' + result.original)
     if result.error:
         print('Error: ' + result.error)
     else:
         print('Final URL: ' + result.final)
         print('Status code: ' + str(result.status))
     print('')
