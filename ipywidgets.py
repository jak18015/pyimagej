import ipywidgets

def _axis_index(image, *options):
    axes = tuple(d for d in range(image.ndim) if image.dims[d].lower() in options)
    if len(axes) == 0:
        raise ValueError(f'Image has no {options[0]} axis.')
    return axes[0]

def ndshow(image, cmap=None, x_axis=None, y_axis=None, immediate=False):
    if not hasattr(image, 'dims'):
        #We need dimensional axis labels
        raise TypeError('Metadata-rich image required.')

    # Infer X and Y if needed
    if x_axis is None:
        x_axis = _axis_index(image, "x", "col")
    if y_axis is None:
        y_axis = _axis_index(image, "y", "row")

    # Build ipywidgets sliders, one per non-planar direction
    widgets = {}
    for d in range(image.ndim):
        if d == x_axis or d == y_axis:
            continue
        label = image.dims[d]
        widgets[label] = ipywidgets.IntSlider(description=label, max=image.shape[d]-1, continuous_update=immediate)

    # Create image plot with interactive sliders
    def recalc(**kwargs):
        print('displaying')
        ij.py.show(plane(image,kwargs), cmap=cmap)
    ipywidgets.interact(recalc, **widgets)

# Display data with ipywidgets

## ndshow(dataset)