from easygui import enterbox

# For now we'll do it this way. Once Gooey implements a way to detect if we're
# actually using the GUI, I'll use that to determine whether to use input() or
# enterbox().
def user_input(message):
    return(enterbox(message))