import numpy as n

from sklearn.discriminant_analysis import (LinearDiscriminantAnalysis,
                                           QuadraticDiscriminantAnalysis)
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cross_validation import (StratifiedKFold, KFold,
                                      StratifiedShuffleSplit, ShuffleSplit,
                                      cross_val_score, permutation_test_score)
from sklearn.metrics import accuracy_score
from joblib import Parallel, delayed

__all__ = ['classify',
           'defClf',
           'defCv'
           ]


class classify(object):
    """Define a classification object and apply to classify data.
    This class can be consider as a centralization of scikit-learn
    tools, with a few more options.

    To classify data, two objects are necessary :
    - A classifier object (lda, svm, knn...)
    - A cross-validation object which is used to validate a classification
    performance.
    This two objects can either be defined before the classify object with
    defCv and defClf, or they can be directly defined inside the classify
    class.

    Parameters
    ----------
    y : array
        The vector label

    clf : int / string / classifier object, optional, [def : 0]
        Define a classifier. If clf is an integer or a string, the
        classifier will be defined inside classify. Otherwise, it is
        possible to define a classifier before with defClf and past it in clf.

    cvtype : string / cross-validation object, optional, [def : 'skfold']
        Define a cross-validation. If cvtype is a string, the
        cross-validation will be defined inside classify. Otherwise, it is
        possible to define a cross-validation before with defCv and past it
        in cvtype.

    clfArg : dictionnary, optional, [def : {}]
        This dictionnary can be used to define supplementar arguments for the
        classifier. See the documentation of defClf.

    cvArg : dictionnary, optional, [def : {}]
        This dictionnary can be used to define supplementar arguments for the
        cross-validation. See the documentation of defCv.

    Return
    ----------
    A object with the following methods :
    -> fit() : to apply the classification object to a dataset
    -> stat() : get the statistical significiance of decoding accuracy
    -> plot() : quick plot of the decoding accuracy

    Example
    ----------
    1) Define a classifier and a cross-validation before classify():

        # Define a 50 times 5-folds cross-validation :
        cv = defCv(y, cvtype='kfold', rep=50, n_folds=5)
        # Define a Random Forest with 200 trees :
        clf = defClf(y, clf='rf', n_tree=200, random_state=100)
        # Past the two objects inside classify :
        clfObj = classify(y, clf=clf, cvtype=cv)

    2) Define a classifier and a cross-validation inside classify():
        clfObj = classify(y, clf = 'rf', cvtype = 'kfold',
                          clfArg = {'n_tree':200, 'random_state':100},
                          cvArg = {'rep':50, 'n_folds':5}
                         )
    1) and 2) are equivalent. Then use clfObj.fit() to classify data.
    """

    def __init__(self, y, clf='lda', cvtype='skfold', clfArg={}, cvArg={}):
        self.y = y
        # Define clf if it's not defined :
        if isinstance(clf, (int, str)):
            clf = defClf(y, clf=clf, **clfArg)
        self.clf = clf
        # Define cv if it's not defined :
        if isinstance(cvtype, str):
            cvtype = defCv(y, cvtype=cvtype, **cvArg)
        self.cv = cvtype

    def __str__(self):
        return str(self.cv[0].lgStr)+' with a '+str(self.clf.lgStr)

    def fit(self, x, xcol='sf', n_jobs=-1):
        """Apply the classification and cross-validation objects to the array x.
        this method return an array containing the decoding accuracy. The
        dimension of this arry depend of the input x.

        Parameters
        ----------
        x : array
            Data to classify. Consider that x.shape = (N, M), N is the number
            of trials (which should be the length of y). M, the number of
            colums, is a supplementar dimension for classifying data. If M = 1,
            the data is consider as a single feature. If M > 1, use the
            parameter xcol to say if x should be consider as a single feature
            (xcol='sf') or multi-features (xcol='mf')

        xcol : string, optional, [def : 'sf']
            If xcol='mf', the returned decoding accuracy (da) will have a
            shape of (1, rep) where rep, is the number of repetitions.
            This mean that all the features are used together. If xcol='sf',
            da.shape = (M, rep), where M is the number of columns of x.

        n_jobs : integer, optional, [def : -1]
            Control the number of jobs to cumpute the decoding accuracy. If
            n_jobs = -1, all the jobs are used.

        Returns
        ----------
        An array containing the decoding accuracy.

        """
        # Check the inputs size :
        x, y = checkXY(x, self.y, xcol)
        rep, nfeat = len(self.cv), len(x)
        # Jobs management :
        if n_jobs == 1:
            repJobs, featJobs = 1, 1
        else:
            if rep < nfeat:
                featJobs, repJobs = n_jobs, 1
            else:
                repJobs, featJobs = n_jobs, 1
        # Run the optimized classification :
        da = Parallel(n_jobs=featJobs)(
            delayed(_classifyRep)(k, y, self.clf, self.cv, repJobs) for k in x)

        return n.array(da)

    def stat(self):
        pass

    def plot(self):
        pass


def _classifyRep(x, y, clf, cv, repJobs):
    """Classify repetitions in parallel
    """
    return Parallel(n_jobs=repJobs)(delayed(
        _cvscore)(x, y, clf, k) for k in cv)


def _cvscore(x, y, clf, cvS):
    """Get the decoding accuracy of one cross-validation
    """
    predictions = []
    ypred = []
    for trainidx, testidx in cvS:
        xtrain, xtest = x[trainidx, ...], x[testidx, ...]
        ytrain, ytest = y[trainidx, ...], y[testidx, ...]
        clf.fit(xtrain, ytrain)
        predictions.extend(clf.predict(xtest))
        ypred.extend(ytest)
    return 100*accuracy_score(ypred, predictions)


class defClf(object):

    """Choose a classifier and switch easyly between classifiers
    implemented in scikit-learn.

    Parameters
    ----------
    y : array
        The vector label

    clf : int or string, optional, [def : 0]
        Define a classifier. Use either an integer or a string
        [Example : classifier='lda' or 0].
        Choose between :
            - 0 / 'lda': Linear Discriminant Analysis (LDA)
            - 1 / 'svm' : Support Vector Machine (SVM)
            - 2 / 'linearsvm' : Linear SVM
            - 3 / 'nusvm' : Nu SVM
            - 4 / 'nb' : Naive Bayesian
            - 5 / 'knn' : k-Nearest Neighbor
            - 6 / 'rf' : Random Forest
            - 7 / 'lr' : Logistic Regression
            - 8 / 'qda' : Quadratic Discriminant Analysis

    kern : string, optional, [def : 'rbf']
        Kernel of the 'svm' classifier

    n_knn : int, optional, [def : 10]
        Number of neighbors for the 'knn' classifier

    n_tree : int, optional, [def : 100]
        Number of trees for the 'rf' classifier

    **kwargs : optional arguments. To define other parameters,
    see the description of scikit-learn.

    Return
    ----------
    A scikit-learn classification objects with two supplementar arguments :
        - lgStr : long description of the classifier
        - shStr : short description of the classifier
    """

    def __init__(self, y, clf='lda', kern='rbf', n_knn=10, n_tree=100,
                 priors=False, **kwargs):
        pass

    def __str__(self):
        return self.lgStr

    def __new__(self, y, clf='lda', kern='rbf', n_knn=10, n_tree=100,
                priors=False, **kwargs):

        # Default value for priors :
        priors = n.array([1/len(n.unique(y))]*len(n.unique(y)))

        if isinstance(clf, str):
            clf = clf.lower()

        # LDA :
        if clf == 'lda' or clf == 0:
            clfObj = LinearDiscriminantAnalysis(
                priors=priors, **kwargs)
            clfObj.lgStr = 'Linear Discriminant Analysis'
            clfObj.shStr = 'LDA'

        # SVM : ‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’, ‘precomputed’ or a callable
        elif clf == 'svm' or clf == 1:
            clfObj = SVC(kernel=kern, probability=True, **kwargs)
            clfObj.lgStr = 'Support Vector Machine (kernel=' + kern + ')'
            clfObj.shStr = 'SVM-' + kern

        # Linear SVM:
        elif clf == 'linearsvm' or clf == 2:
            clfObj = LinearSVC(**kwargs)
            clfObj.lgStr = 'Linear Support Vector Machine'
            clfObj.shStr = 'LSVM'

        # Nu SVM :
        elif clf == 'nusvm' or clf == 3:
            clfObj = NuSVC(**kwargs)
            clfObj.lgStr = 'Nu Support Vector Machine'
            clfObj.shStr = 'NuSVM'

        # Naive Bayesian :
        elif clf == 'nb' or clf == 4:
            clfObj = GaussianNB(**kwargs)
            clfObj.lgStr = 'Naive Baysian'
            clfObj.shStr = 'NB'

        # KNN :
        elif clf == 'knn' or clf == 5:
            clfObj = KNeighborsClassifier(n_neighbors=n_knn, **kwargs)
            clfObj.lgStr = 'k-Nearest Neighbor (neighbor=' + str(n_knn) + ')'
            clfObj.shStr = 'KNN-' + str(n_knn)

        # Random forest :
        elif clf == 'rf' or clf == 6:
            clfObj = RandomForestClassifier(n_estimators=n_tree, **kwargs)
            clfObj.lgStr = 'Random Forest (tree=' + str(n_tree) + ')'
            clfObj.shStr = 'RF-' + str(n_tree)

        # Logistic regression :
        elif clf == 'lr' or clf == 7:
            clfObj = LogisticRegression(**kwargs)
            clfObj.lgStr = 'Logistic Regression'
            clfObj.shStr = 'LogReg'

        # QDA :
        elif clf == 'qda' or clf == 8:
            clfObj = QuadraticDiscriminantAnalysis(**kwargs)
            clfObj.lgStr = 'Quadratic Discriminant Analysis'
            clfObj.shStr = 'QDA'

        return clfObj


class defCv(object):

    """Choose a cross_validation (CV) and switch easyly between
    CV implemented in scikit-learn.

    Parameters
    ----------
    y : array
        The vector label

    cvtype : string, optional, [def : skfold]
        Define a cross_validation. Choose between :
            - 'skfold' : Stratified k-Fold
            - 'kfold' : k-fold
            - 'sss' : Stratified Shuffle Split
            - 'ss' : Shuffle Split

    n_folds : integer, optional, [def : 10]
        Number of folds

    rndstate : integer, optional, [def : 0]
        Define a random state. Usefull to replicate a result

    rep : integer, optional, [def : 10]
        Number of repetitions

    **kwargs : optional arguments. To define other parameters,
    see the description of scikit-learn.

    Return
    ----------
    A list of scikit-learn cross-validation objects with two supplementar
    arguments :
        - lgStr : long description of the cross_validation
        - shStr : short description of the cross_validation
    """

    def __init__(self, y, cvtype='skfold', n_folds=10, rndstate=0, rep=10,
                 **kwargs):
        pass

    def __str__(self):
        return self.lgStr

    def __new__(self, y, cvtype='skfold', n_folds=10, rndstate=0, rep=10,
                **kwargs):
        y = n.ravel(y)
        return [_define(y, cvtype=cvtype, n_folds=n_folds, rndstate=k, rep=rep,
                        **kwargs) for k in range(rep)]


def _define(y, cvtype='skfold', n_folds=10, rndstate=0, rep=10,
            **kwargs):
    # Stratified k-fold :
    if cvtype == 'skfold':
        cvT = StratifiedKFold(y, n_folds=n_folds, shuffle=True,
                              random_state=rndstate, **kwargs)
        cvT.lgStr = str(rep)+'-times, '+str(n_folds)+' Stratified k-folds'
        cvT.shStr = str(rep)+'rep x'+str(n_folds)+' '+cvtype

    # k-fold :
    elif cvtype == 'kfold':
        cvT = KFold(len(y), n_folds=n_folds, shuffle=True,
                    random_state=rndstate, **kwargs)
        cvT.lgStr = str(rep)+'-times, '+str(n_folds)+' k-folds'
        cvT.shStr = str(rep)+'rep x'+str(n_folds)+' '+cvtype

    # Shuffle stratified k-fold :
    elif cvtype == 'sss':
        cvT = StratifiedShuffleSplit(y, n_iter=n_folds,
                                     test_size=1/n_folds,
                                     random_state=rndstate, **kwargs)
        cvT.lgStr = str(rep)+'-times, test size 1/' + \
            str(n_folds)+' Shuffle Stratified Split'
        cvT.shStr = str(rep)+'rep x'+str(n_folds)+' '+cvtype

    # Shuffle stratified :
    elif cvtype == 'ss':
        cvT = ShuffleSplit(len(y), n_iter=rep, test_size=1/n_folds,
                           random_state=rndstate, **kwargs)
        cvT.lgStr = str(rep)+'-times, test size 1/' + \
            str(n_folds)+' Shuffle Stratified'
        cvT.shStr = str(rep)+'rep x'+str(n_folds)+' '+cvtype

    return cvT


def checkXY(x, y, x_col):
    """Prepare the inputs x and y
    """
    x, y = n.matrix(x), n.ravel(y)
    if x.shape[0] is not len(y):
        x = x.T
    if x_col == 'mf':
        x = [x]
    elif x_col == 'sf':
        x = [n.array(x[:, k]) for k in range(x.shape[1])]
    return x, y
