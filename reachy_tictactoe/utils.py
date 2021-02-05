piece2id = {
    'cube': 2,
    'cylinder': 0,
    'none': 1,
}

id2piece = {
    v: k for k, v in piece2id.items()
}

piece2player = {
    'cube': 'human',
    'cylinder': 'robot',
    'none': 'nobody',
}
