import React, { Component } from 'react';

interface Props {
    username: string,
}

interface State {
    prevLine?: string,
    prevAuthor?: string,
    currLine: string,
}

export default class WriteStory extends Component<Props, State> {
    constructor(props: Props) {
        super(props);

        this.state = {
            currLine: '',
        }
    }

    render() {
        const { username } = this.props;
        return null;
    }
}