from src.decision_tree_bridge import fill_tree_noninteractive


def test_fill_tree_noninteractive_basic():
    reco, missing = fill_tree_noninteractive('patiente 34 ans céphalées')
    assert reco is None
    assert isinstance(missing, list)
    assert 'Fièvre ?' in missing[0] or 'Fièvre' in missing[0]
