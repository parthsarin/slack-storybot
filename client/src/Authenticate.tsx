import React, { FunctionComponent, KeyboardEvent, useState } from 'react';
import { Alert, Button, Container, FormControl } from 'react-bootstrap';
import axios from 'axios';
import { User } from './App';

interface Props {
    onSubmit: (slackUser: User) => void,
    newUser: boolean
}

interface UserQueryResponse {
    hasError: boolean,
    error?: string,
    user?: User
}

const cleanName = (username: string): string => {
    // Strips the @ signs from the beginning of the string and trailing
    // whitespace.
    let output: string = username.trim();           // whitespace
    output = output.replace(new RegExp("^@+"), ""); // @ signs at the front
    
    return output
}

const getUser = (username: string): Promise<UserQueryResponse> => {
    /* Gets the full user by querying the backend */
    return axios
        .post('/api/verify_username', { username })
        .then(response => response.data)
        .then((data) => {
            if (data.error) {
                return {
                    hasError: true,
                    error: data.error
                }
            } else {
                return {
                    hasError: false,
                    user: data.user as User
                }
            }
        })
}

const Authenticate: FunctionComponent<Props> = ({ onSubmit, newUser }) => {
    const [username, setUsername] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const greeting = newUser 
                     ? "Hi, I don't think we've met! 👋" 
                     : "So, you're an imposter, huh? 👀";

    const fullSubmit = (username: string) => {
        getUser(cleanName(username))
            .then((queryResponse) => {
                if (queryResponse.hasError) {
                    setError(queryResponse.error!);
                } else {
                    onSubmit(queryResponse.user!);
                }
            })
    }
    
    return (
        <Container className="mt-2 mb-2">
            <h1>{greeting}</h1>
            <p className="lead">Could you tell me what your Slack username is?</p>

            <p>
                This is the handle that people can use to refer to you after the
                @ sign. For example, I'm <code>@Parth</code>. Head over to Slack
                and type '@' into a message box, then search for yourself. 
                Select the correct profile by clicking on it or pressing Enter
                and then paste the content of the message box here.
            </p>

            {
                error
                ? <Alert variant='danger'>
                    <p className="mb-0">{error}</p>
                </Alert>
                : null
            }

            <FormControl
                value={username}
                placeholder="@Parth"
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e: KeyboardEvent<HTMLInputElement>) => {
                    if (e.code === 'Enter') {
                        fullSubmit(username);
                    }
                }}
            />

            <Button
                variant='primary'
                className="mt-2 float-right"
                onClick={() => fullSubmit(username)}
            >
                Submit
            </Button>
        </Container>
    );
}

export default Authenticate;