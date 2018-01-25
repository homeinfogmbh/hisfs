"""File system policy."""


def to_path(nodes):
    """Converts the nodes into a path string."""

    return PATHSEP + PATHSEP.join(nodes)


class Path:
    """Represents the path to a file or directory."""

    def __init__(self, path):
        """Sets the path string."""
        self.path = path

    def __iter__(self):
        """Yields the respective nodes."""
        yield from self.nodes

    @property
    def nodes(self):
        """Yields the path nodes."""
        if self.path.startswith(PATHSEP):
            return self.path.split(PATHSEP)[1:]

        return self.path.split(PATHSEP)


class UserInode:
    """Inode wrapper with user and group context."""

    def __init__(self, path, user, group):
        """Sets user and group."""
        self.path = Path(path)
        self.user = user
        self.group = Group

    @property
    def context_expression(self):
        """Returns the filering expression for this user context."""
        return (Inode.owner == self.user) | (Inode.group == self.group)

    @property
    def inodes(self):
        """Returns the respective Inodes."""
        *parents, inode = self.path
        processed = []
        parent = None

        for parent_name in parents:
            processed.append(parent_name)

            if parent is None:
                parent_expression = Inode.parent >> None
            else:
                parent_expression = Inode.parent == parent

            try:
                parent = Inode.get(
                    (Inode.name == parent_name) & parent_expression
                    & self.context_expression)
            except Inode.DoesNotExist:
                raise NoSuchInode(to_path(processed))

            yield parent

        try:
            parent = Inode.get(
                (Inode.name == parent_name) & parent_expression
                & self.context_expression)
        except Inode.DoesNotExist:
            raise NoSuchInode(path(processed))

    def read(self, file):
        """Reads the respective file."""
        if not file.is_file:
            raise NotAFile(file)

        for parent in file.parents:
            if not parent.executable_by(self.user, self.group):
                raise NotExecutable(parent)

        if file.readable_by(self.user, self.group):
            return file.data

        raise NotReadable(file)

    def list(self, inode):
        """Lists the respective Inode."""
        for parent in inode.parents:
            if not parent.executable_by(self.user, self.group):
                raise NotExecutable(parent)

        if inode.readable_by(self.user, self.group):
            return inode.to_dict()

        raise NotReadable(inode)

    def write(self, data, directory, filename):
        """Writes data to the directory."""
        if not directory.is_dir:
            raise NotADirectory(directory)

        for parent in directory.parents:
            if not parent.executable_by(self.user, self.group):
                raise NotExecutable(parent)

        if not directory.executable_by(self.user, self.group):
            raise NotExecutable(directory)

        try:
            file = directory.get_child(filename)
        except DoesNotExist:
            if directory.writable_by(self.user, self.group):
                return Inode.add_file(directory, data, filename)

            raise NotWritable(directory)

        if file.is_file:
            if file.writable_by(directory, data, filename):
                file.data = data
                return file

            raise NotWritable(file)

        raise NotAFile(file)
