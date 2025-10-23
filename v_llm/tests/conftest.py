import sys, os
# Ajouter la racine du projet et le dossier src dans sys.path pour les tests
root = os.path.dirname(os.path.dirname(__file__))
if root not in sys.path:
    sys.path.insert(0, root)
src_dir = os.path.join(root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
